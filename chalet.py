
import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta
import os

# إعداد واجهة التطبيق لتناسب الهاتف والكمبيوتر
st.set_page_config(page_title="نظام حجز الشاليه المطور", layout="centered")

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

# الشفتات المتاحة مع الرموز التعبيرية وأوقاتها الثابتة (مع ترك ساعة للتنظيف)
SHIFTS = {
    "يوم كامل 🟡": {"from": time(14, 0), "to": time(11, 0)},
    "شفت صباحي ⛅": {"from": time(9, 0), "to": time(16, 0)},     # تنظيف من 16:00 إلى 17:00
    "شفت مسائي 🌙": {"from": time(17, 0), "to": time(23, 0)}
}

# التحقق من وجود قاعدة البيانات وتحديث الأعمدة لتناسب النظام الجديد
REQUIRED_COLUMNS = ["اسم الحاجز", "التاريخ", "اليوم", "الشفت", "وقت الوصول", "وقت الخروج", "المبلغ"]

if os.path.exists(DB_FILE):
    try:
        df_bookings = pd.read_csv(DB_FILE)
        # التأكد من مطابقة الأعمدة للنظام الجديد
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
    # إذا كان اليوم محجوزاً "يوم كامل"، فلا يمكن حجز أي شفت فيه
    # وإذا كان الشفت المطلوب محجوزاً بالفعل، يمنع الحجز
    match = df_bookings[(df_bookings["التاريخ"] == date_str) & 
                        ((df_bookings["الشفت"] == shift_name) | (df_bookings["الشفت"] == "يوم كامل 🟡") | (shift_name == "يوم كامل 🟡"))]
    return not match.empty

# تقسيم التطبيق إلى تبويبين متطابقين في الصلاحيات والمظهر (واحد لك وواحد للمالك)
tab1, tab2 = st.tabs(["👤 شاشتي (تسجيل حجز جديد)", "👑 شاشة المالك (التقويم والحجوزات)"])

# --- نموذج الحجز الموحد (نفس المنطق للطرفين) ---
def render_booking_form(user_role):
    st.header(f"✍️ حجز جديد من قبل: {user_role}")
    
    # 1. اختيار التاريخ من التقويم في الأعلى
    booking_date = st.date_input(f"اختر تاريخ الحجز ({user_role}):", min_value=datetime.today(), key=f"date_{user_role}")
    date_str = booking_date.strftime('%Y-%m-%d')
    day_name_ar = DAYS_ARABIC[booking_date.strftime('%A')]
    
    # عرض اسم اليوم المختار بشكل واضح تحت التقويم
    st.write(f"📅 اليوم المختار: **{day_name_ar}**")
    
    # 2. اختيار نوع الشفت مع الرموز الجميلة
    selected_shift = st.radio("اختر الشفت المطلوب:", list(SHIFTS.keys()), key=f"shift_{user_role}")
    
    # عرض صناديق وقت الوصول ووقت الخروج تلقائياً بناءً على الشفت
    arrival_time = SHIFTS[selected_shift]["from"]
    departure_time = SHIFTS[selected_shift]["to"]
    
    col1, col2 = st.columns(2)
    with col1:
        st.text_input("⏳ صندوق وقت الوصول (تلقائي):", value=arrival_time.strftime('%H:%M'), disabled=True, key=f"arr_{user_role}")
    with col2:
        st.text_input("⏳ صندوق وقت الخروج (تلقائي):", value=departure_time.strftime('%H:%M'), disabled=True, key=f"dep_{user_role}")
    
    # 3. إدخال الاسم والمبلغ
    customer_name = st.text_input("اسم الزبون / الجهة الحاجزة:", key=f"name_{user_role}")
    amount = st.number_input("المبلغ المتفق عليه (دينار):", min_value=0, step=10, key=f"amount_{user_role}")
    
    # زر الحفظ
    submit = st.button("تأكيد وحفظ الحجز في السحابة", key=f"btn_{user_role}", use_container_width=True)
    
    if submit:
        if not customer_name:
            st.error("❌ الرجاء إدخال اسم الزبون لتثبيت الحجز.")
        elif is_already_booked(date_str, selected_shift):
            st.error(f"⚠️ عذراً! هذا اليوم أو الشفت محجوز مسبقاً. يرجى مراجعة التقويم واختيار وقت آخر.")
        else:
            # تجهيز السجل الجديد
            new_booking = {
                "اسم الحاجز": customer_name,
                "التاريخ": date_str,
                "اليوم": day_name_ar,
                "الشفت": selected_shift,
                "وقت الوصول": arrival_time.strftime('%H:%M'),
                "وقت الخروج": departure_time.strftime('%H:%M'),
                "المبلغ": amount
            }
            global df_bookings
            df_bookings = pd.concat([df_bookings, pd.DataFrame([new_booking])], ignore_index=True)
            df_bookings.to_csv(DB_FILE, index=False)
            st.success(f"✅ تم تسجيل الحجز بنجاح ليوم {day_name_ar} ({selected_shift})")
            st.rerun()

# --- لوحة عرض التقويم الملونة والأيام المحجوزة الموحدة ---
def render_calendar_view(info_text):
    st.subheader("📊 تقويم الحجوزات الذكي")
    st.info(info_text)
    
    if df_bookings.empty:
        st.success("🟢 جميع الأيام والشفتات شاغرة ومتاحة للحجز حالياً!")
    else:
        # تجهيز جدول العرض النظيف (بدون إظهار الأسماء أو المبالغ لحفظ الخصوصية وتجنب اللبس)
        df_display = df_bookings.copy()
        
        # إضافة علامة الصح الأخضر وجعلها واضحة جداً بالجدول لتبين الحالة المحجوزة
        df_display["الحالة"] = "🔴 محجوز ومغلق"
        
        # ترتيب وتصفية الأعمدة المعروضة فقط
        df_display = df_display[["التاريخ", "اليوم", "الشفت", "وقت الوصول", "وقت الخروج", "الحالة"]]
        
        # ترتيب الحجوزات من الأحدث فالأقدم حسب التاريخ
        df_display = df_display.sort_values(by="التاريخ")
        
        # عرض جدول الحجوزات الآمن
        st.dataframe(df_display, use_container_width=True, hide_index=True)

# --- تشغيل تبويب المستخدم (أنت) ---
with tab1:
    render_booking_form(user_role="المستخدم الأساسي")
    st.markdown("---")
    render_calendar_view("راجع الأيام المحجوزة بالأسفل باللون الأحمر لتتجنب تضارب حجوزاتك مع المالك.")

# --- تشغيل تبويب المالك ---
with tab2:
    render_booking_form(user_role="المالك")
    st.markdown("---")
    render_calendar_view("هذه الشاشة مخصصة لك يا صاحب الشاليه لمتابعة الشفتات والأيام المحجوزة من قبلك أو من قِبل المشغل.")
