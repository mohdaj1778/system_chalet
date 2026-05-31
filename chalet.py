import streamlit as st
import pandas as pd
from datetime import datetime, time
import os

# إعداد واجهة التطبيق لتناسب الهاتف والكمبيوتر
st.set_page_config(page_title="نظام حجز الشاليه الذكي", layout="centered")

st.title("🏡 نظام إدارة وحجوزات الشاليه الذكي")

# اسم ملف قاعدة البيانات
DB_FILE = "chalet_bookings.csv"

# قاموس لتحويل أسماء الأيام إلى العربية
DAYS_ARABIC = {
    "Monday": "الإثنين",
    "Tuesday": "الثلاثاء",
    "Wednesday": "الأربعاء",
    "Thursday": "الخميس",
    "Friday": "الجمعة",
    "Saturday": "السبت",
    "Sunday": "الأحد"
}

# الشفتات الافتراضية مع ساعات كاملة بدون دقائق
SHIFTS = {
    "يوم كامل 🟡": {"from": 14, "to": 11},
    "شفت صباحي ⛅": {"from": 10, "to": 21},
    "شفت مسائي 🌙": {"from": 22, "to": 9}
}

# التحقق من وجود قاعدة البيانات وتحديث الأعمدة
REQUIRED_COLUMNS = ["اسم الحاجز", "التاريخ", "اليوم", "الشفت", "وقت الوصول", "وقت الخروج", "المبلغ"]

if os.path.exists(DB_FILE):
    try:
        df_bookings = pd.read_csv(DB_FILE)
        # التأكد من خلو ملف الأرقام من أي مشاكل في الفهرسة
        df_bookings.reset_index(drop=True, inplace=True)
    except:
        df_bookings = pd.DataFrame(columns=REQUIRED_COLUMNS)
else:
    df_bookings = pd.DataFrame(columns=REQUIRED_COLUMNS)

# دالة للتحقق من تضارب الحجوزات
def is_already_booked(date_str, shift_name):
    if df_bookings.empty:
        return False
    match = df_bookings[(df_bookings["التاريخ"] == date_str) & 
                        ((df_bookings["الشفت"] == shift_name) | (df_bookings["الشفت"] == "يوم كامل 🟡") | (shift_name == "يوم كامل 🟡"))]
    return not match.empty

# تقسيم التطبيق إلى تبويبين
tab1, tab2 = st.tabs(["📝 تسجيل حجز جديد (المشغل)", "📊 شاشة صاحب الشاليه"])

# --- القسم الأول: شاشة المشغل (باسورد 4321) ---
with tab1:
    st.header("👤 الدخول إلى شاشة الحجوزات")
    user_pass = st.text_input("أدخل كلمة مرور المشغل للدخول:", type="password", key="pass_user")
    
    if user_pass == "4321":
        st.success("🔓 تم الدخول بنجاح")
        
        st.subheader("✍️ إضافة حجز جديد")
        booking_date = st.date_input("اختر تاريخ الحجز:", min_value=datetime.today(), key="date_u")
        date_str = booking_date.strftime('%Y-%m-%d')
        day_name_ar = DAYS_ARABIC[booking_date.strftime('%A')]
        st.write(f"📅 اليوم المختار: **{day_name_ar}**")
        
        # اختيار الشفت
        selected_shift = st.radio("اختر الشفت المطلوب:", list(SHIFTS.keys()), key="shift_u")
        
        default_from = SHIFTS[selected_shift]["from"]
        default_to = SHIFTS[selected_shift]["to"]
        
        # صناديق اختيار الوقت (ساعات كاملة باستخدام الأرقام فقط وبدون دقائق)
        col1, col2 = st.columns(2)
        with col1:
            hour_from = st.number_input("⏳ ساعة الوصول (توقيت 24 ساعة):", min_value=0, max_value=23, value=default_from, step=1, key="hour_from_u")
        with col2:
            hour_to = st.number_input("⏳ ساعة الخروج (توقيت 24 ساعة):", min_value=0, max_value=23, value=default_to, step=1, key="hour_to_u")
        
        customer_name = st.text_input("اسم الزبون الفلاني:", key="cust_name_u")
        amount = st.number_input("المبلغ المطلوب (بكذا من المال):", min_value=0, step=10, key="amount_u")
        
        submit_button = st.button("حفظ وتأكيد الحجز", key="submit_u", use_container_width=True)
        
        if submit_button:
            if not customer_name:
                st.error("الرجاء إدخال اسم الزبون")
            elif is_already_booked(date_str, selected_shift):
                st.error("⚠️ عذراً! هذا اليوم أو الشفت محجوز مسبقاً في التقويم.")
            else:
                new_data = {
                    "اسم الحاجز": customer_name,
                    "التاريخ": date_str,
                    "اليوم": day_name_ar,
                    "الشفت": selected_shift,
                    "وقت الوصول": f"{hour_from}:00",
                    "وقت الخروج": f"{hour_to}:00",
                    "المبلغ": amount
                }
                df_bookings = pd.concat([df_bookings, pd.DataFrame([new_data])], ignore_index=True)
                df_bookings.to_csv(DB_FILE, index=False)
                st.success(f"✅ تم تسجيل حجز {customer_name} بنجاح!")
                st.rerun()
                    
        st.markdown("---")
        st.subheader("📊 جدول الحجوزات والمالية الكامل (المشغل)")
        if df_bookings.empty:
            st.info("لا توجد حجوزات مسجلة حالياً.")
        else:
            # عرض الحجوزات مع ميزة الحذف الذكية بجانب كل سطر
            for idx, row in df_bookings.iterrows():
                col_info, col_del = st.columns([5, 1])
                with col_info:
                    st.write(f"📅 **{row['التاريخ']} ({row['اليوم']})** | {row['الشفت']} | من الساعة {row['وقت الوصول']} إلى {row['وقت الخروج']} | الزبون: {row['اسم الحاجز']} | المبلغ: {row['المبلغ']} دينار")
                with col_del:
                    if st.button("❌ إلغاء", key=f"del_u_{idx}"):
                        df_bookings = df_bookings.drop(idx).reset_index(drop=True)
                        df_bookings.to_csv(DB_FILE, index=False)
                        st.success("تم إلغاء الحجز بنجاح!")
                        st.rerun()
                        
            st.markdown("---")
            total_money = df_bookings["المبلغ"].astype(float).sum()
            st.metric(label="💰 إجمالي الإيرادات المسجلة", value=f"{total_money} دينار")
            
    elif user_pass != "":
        st.error("❌ كلمة المرور غير صحيحة!")

# --- القسم الثاني: شاشة المالك (باسورد 1234) ---
with tab2:
    st.header("👑 الدخول إلى شاشة المالك")
    owner_pass = st.text_input("أدخل كلمة مرور المالك للدخول:", type="password", key="pass_owner")
    
    if owner_pass == "1234":
        st.success("🔓 تم الدخول بنجاح")
        
        st.subheader("✍️ تثبيت حجز من طرف المالك")
        booking_date_o = st.date_input("اختر تاريخ الحجز:", min_value=datetime.today(), key="date_o")
        date_str_o = booking_date_o.strftime('%Y-%m-%d')
        day_name_ar_o = DAYS_ARABIC[booking_date_o.strftime('%A')]
        st.write(f"📅 اليوم المختار: **{day_name_ar_o}**")
        
        # اختيار الشفت للمالك
        selected_shift_o = st.radio("اختر الشفت المطلوب:", list(SHIFTS.keys()), key="shift_o")
        
        default_from_o = SHIFTS[selected_shift_o]["from"]
        default_to_o = SHIFTS[selected_shift_o]["to"]
        
        # صناديق الساعات للمالك
        col1, col2 = st.columns(2)
        with col1:
            hour_from_o = st.number_input("⏳ ساعة الوصول (توقيت 24 ساعة):", min_value=0, max_value=23, value=default_from_o, step=1, key="hour_from_o")
        with col2:
            hour_to_o = st.number_input("⏳ ساعة الخروج (توقيت 24 ساعة):", min_value=0, max_value=23, value=default_to_o, step=1, key="hour_to_o")
        
        submit_button_o = st.button("تأكيد الحجز من قِبل المالك", key="submit_o", use_container_width=True)
        
        if submit_button_o:
            if is_already_booked(date_str_o, selected_shift_o):
                st.error("⚠️ عذراً! هذا اليوم أو الشفت محجوز مسبقاً في التقويم.")
            else:
                new_data_o = {
                    "اسم الحاجز": "محجوز من المالك",
                    "التاريخ": date_str_o,
                    "اليوم": day_name_ar_o,
                    "الشفت": selected_shift_o,
                    "وقت الوصول": f"{hour_from_o}:00",
                    "وقت الخروج": f"{hour_to_o}:00",
                    "المبلغ": 0
                }
                df_bookings = pd.concat([df_bookings, pd.DataFrame([new_data_o])], ignore_index=True)
                df_bookings.to_csv(DB_FILE, index=False)
                st.success(f"✅ تم تأكيد حجز المالك بنجاح!")
                st.rerun()
                    
        st.markdown("---")
        st.subheader("📊 تقويم الحجوزات العام (رؤية المالك الآمنة مع ميزة الإلغاء)")
        if df_bookings.empty:
            st.info("🟢 جميع الأيام والشفتات شاغرة ومتاحة للحجز حالياً!")
        else:
            # عرض الحجوزات الآمنة للمالك مع إمكانية الإلغاء والحذف لحجوزاته
            for idx, row in df_bookings.iterrows():
                col_info_o, col_del_o = st.columns([5, 1])
                with col_info_o:
                    st.write(f"📅 **{row['التاريخ']} ({row['اليوم']})** | {row['الشفت']} | من الساعة {row['وقت الوصول']} إلى {row['وقت الخروج']} | الحالة: 🔴 محجوز ومغلق")
                with col_del_o:
                    if st.button("❌ إلغاء", key=f"del_o_{idx}"):
                        df_bookings = df_bookings.drop(idx).reset_index(drop=True)
                        df_bookings.to_csv(DB_FILE, index=False)
                        st.success("تم إلغاء الحجز المحدّد!")
                        st.rerun()
            
    elif owner_pass != "":
        st.error("❌ كلمة المرور غير صحيحة!")
