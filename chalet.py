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

# تعديل الشفتات بناءً على رؤيتك الصحيحة (اليوم الكامل ينتهي بنفس اليوم)
SHIFTS = {
    "يوم كامل 🟡": {"from": time(10, 0), "to": time(21, 0)},
    "شفت صباحي ⛅": {"from": time(10, 0), "to": time(16, 0)},
    "شفت مسائي 🌙": {"from": time(17, 0), "to": time(23, 0)}
}

# التحقق من وجود قاعدة البيانات وتحديث الأعمدة لتناسب النظام الجديد
REQUIRED_COLUMNS = ["اسم الحاجز", "التاريخ", "اليوم", "الشفت", "وقت الوصول", "وقت الخروج", "المبلغ"]

if os.path.exists(DB_FILE):
    try:
        df_bookings = pd.read_csv(DB_FILE)
        if "الشفت" not in df_bookings.columns:
            df_bookings = pd.DataFrame(columns=REQUIRED_COLUMNS)
    except:
        df_bookings = pd.DataFrame(columns=REQUIRED_COLUMNS)
else:
    df_bookings = pd.DataFrame(columns=REQUIRED_COLUMNS)

# دالة للتحقق من تضارب الحجوزات
def is_already_booked(date_str, shift_name):
    if df_bookings.empty:
        return False
    # التحقق من وجود حجز لنفس اليوم ونفس الشفت، أو وجود حجز "يوم كامل" يغلق اليوم بالكامل
    match = df_bookings[(df_bookings["التاريخ"] == date_str) & 
                        ((df_bookings["الشفت"] == shift_name) | (df_bookings["الشفت"] == "يوم كامل 🟡") | (shift_name == "يوم كامل 🟡"))]
    return not match.empty

# تقسيم التطبيق إلى تبويبين
tab1, tab2 = st.tabs(["📝 تسجيل حجز جديد (المشغل)", "📊 شاشة صاحب الشاليه"])

# --- القسم الأول: شاشتك الخاصة (المشغل) بكلمة مرور 4321 ---
with tab1:
    st.header("👤 الدخول إلى شاشة الحجوزات")
    user_pass = st.text_input("أدخل كلمة مرور المشغل للدخول:", type="password", key="pass_user")
    
    if user_pass == "4321":
        st.success("🔓 تم الدخول بنجاح إلى شاشة المشغل")
        
        # نموذج الحجز الخاص بك بكامل التفاصيل (الاسم والمبلغ)
        with st.form("user_booking_form", clear_on_submit=True):
            st.subheader("✍️ إضافة حجز جديد")
            booking_date = st.date_input("اختر تاريخ الحجز:", min_value=datetime.today(), key="date_u")
            date_str = booking_date.strftime('%Y-%m-%d')
            day_name_ar = DAYS_ARABIC[booking_date.strftime('%A')]
            
            st.write(f"📅 اليوم المختار: **{day_name_ar}**")
            selected_shift = st.radio("اختر الشفت المطلوب:", list(SHIFTS.keys()), key="shift_u")
            
            arrival_time = SHIFTS[selected_shift]["from"]
            departure_time = SHIFTS[selected_shift]["to"]
            
            col1, col2 = st.columns(2)
            with col1:
                st.text_input("⏳ وقت الوصول (تلقائي):", value=arrival_time.strftime('%H:%M'), disabled=True)
            with col2:
                st.text_input("⏳ وقت الخروج (تلقائي):", value=departure_time.strftime('%H:%M'), disabled=True)
            
            customer_name = st.text_input("اسم الزبون الفلاني:")
            amount = st.number_input("المبلغ المطلوب (بكذا من المال):", min_value=0, step=10)
            
            submit_button = st.form_submit_button("حفظ وتأكيد الحجز")
            
            if submit_button:
                if not customer_name:
                    st.error("الرجاء إدخال اسم الزبون")
                elif is_already_booked(date_str, selected_shift):
                    st.error("⚠️ عذراً! هذا اليوم أو الشفت محجوز مسبقاً في التقويم. يرجى اختيار موعد آخر.")
                else:
                    new_data = {
                        "اسم الحاجز": customer_name,
                        "التاريخ": date_str,
                        "اليوم": day_name_ar,
                        "الشفت": selected_shift,
                        "وقت الوصول": arrival_time.strftime('%H:%M'),
                        "وقت الخروج": departure_time.strftime('%H:%M'),
                        "المبلغ": amount
                    }
                    df_bookings = pd.concat([df_bookings, pd.DataFrame([new_data])], ignore_index=True)
                    df_bookings.to_csv(DB_FILE, index=False)
                    st.success(f"✅ تم تسجيل حجز {customer_name} بنجاح!")
                    st.rerun()
                    
        # عرض التقويم وجدول الحجوزات الكامل للمشغل (يحتوي على الأرقام والأسماء)
        st.markdown("---")
        st.subheader("📊 جدول الحجوزات والمالية الكامل (خاص بك)")
        if df_bookings.empty:
            st.info("لا توجد حجوزات مسجلة حالياً.")
        else:
            st.dataframe(df_bookings, use_container_width=True, hide_index=True)
            total_money = df_bookings["المبلغ"].astype(float).sum()
            st.metric(label="💰 إجمالي الإيرادات المسجلة", value=f"{total_money} دينار")
            
    elif user_pass != "":
        st.error("❌ كلمة المرور غير صحيحة!")

# --- القسم الثاني: شاشة المالك بكلمة مرور 1234 (التقويم فقط وبدون بيانات مالية أو أسماء زبائن) ---
with tab2:
    st.header("👑 الدخول إلى شاشة المالك")
    owner_pass = st.text_input("أدخل كلمة مرور المالك للدخول:", type="password", key="pass_owner")
    
    if owner_pass == "1234":
        st.success("🔓 تم الدخول بنجاح إلى شاشة المالك")
        
        # نموذج الحجز الخاص بالمالك (يحجز مباشرة بدون تفاصيل الزبون والمبالغ)
        with st.form("owner_booking_form", clear_on_submit=True):
            st.subheader("✍️ تثبيت حجز من طرف المالك")
            booking_date_o = st.date_input("اختر تاريخ الحجز:", min_value=datetime.today(), key="date_o")
            date_str_o = booking_date_o.strftime('%Y-%m-%d')
            day_name_ar_o = DAYS_ARABIC[booking_date_o.strftime('%A')]
            
            st.write(f"📅 اليوم المختار: **{day_name_ar_o}**")
            selected_shift_o = st.radio("اختر الشفت المطلوب:", list(SHIFTS.keys()), key="shift_o")
            
            arrival_time_o = SHIFTS[selected_shift_o]["from"]
            departure_time_o = SHIFTS[selected_shift_o]["to"]
            
            col1, col2 = st.columns(2)
            with col1:
                st.text_input("⏳ وقت الوصول (تلقائي):", value=arrival_time_o.strftime('%H:%M'), disabled=True, key="arr_o")
            with col2:
                st.text_input("⏳ وقت الخروج (تلقائي):", value=departure_time_o.strftime('%H:%M'), disabled=True, key="dep_o")
            
            submit_button_o = st.form_submit_button("تأكيد الحجز من قِبل المالك")
            
            if submit_button_o:
                if is_already_booked(date_str_o, selected_shift_o):
                    st.error("⚠️ عذراً! هذا اليوم أو الشفت محجوز مسبقاً في التقويم.")
                else:
                    new_data_o = {
                        "اسم الحاجز": "محجوز من المالك",
                        "التاريخ": date_str_o,
                        "اليوم": day_name_ar_o,
                        "الشفت": selected_shift_o,
                        "وقت الوصول": arrival_time_o.strftime('%H:%M'),
                        "وقت الخروج": departure_time_o.strftime('%H:%M'),
                        "المبلغ": 0
                    }
                    df_bookings = pd.concat([df_bookings, pd.DataFrame([new_data_o])], ignore_index=True)
                    df_bookings.to_csv(DB_FILE, index=False)
                    st.success(f"✅ تم تأكيد حجز المالك ليوم {day_name_ar_o} ({selected_shift_o})")
                    st.rerun()
                    
        # عرض التقويم الآمن للمالك (يظهر فقط الأيام المحجوزة بدون تفاصيل مالية أو أسماء الزبائن)
        st.markdown("---")
        st.subheader("📊 تقويم الحجوزات العام والأيام المغلقة")
        if df_bookings.empty:
            st.info("🟢 جميع الأيام والشفتات شاغرة ومتاحة للحجز حالياً!")
        else:
            df_owner_view = df_bookings.copy()
            df_owner_view["الحالة"] = "🔴 محجوز ومغلق"
            # الفلترة وعرض الأعمدة الآمنة فقط لمنع ظهور الاسم والمبلغ للمالك
            df_owner_view = df_owner_view[["التاريخ", "اليوم", "الشفت", "وقت الوصول", "وقت الخروج", "الحالة"]]
            df_owner_view = df_owner_view.sort_values(by="التاريخ")
            st.dataframe(df_owner_view, use_container_width=True, hide_index=True)
            
    elif owner_pass != "":
        st.error("❌ كلمة المرور غير صحيحة!")
