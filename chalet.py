import streamlit as st
import pandas as pd
from datetime import datetime, time
import os

# إعداد واجهة التطبيق لتناسب الهاتف والكمبيوتر
st.set_page_config(page_title="نظام حجز الشاليه", layout="centered")

st.title("🏡 نظام إدارة وحجوزات الشاليه")

# اسم ملف قاعدة البيانات البسيطة (CSV) لضمان حفظ البيانات حتى لو أغلقنا التطبيق
DB_FILE = "chalet_bookings.csv"

# قاموس لتحويل أسماء الأيام إلى اللغة العربية
DAYS_ARABIC = {
    "Monday": "الإثنين",
    "Tuesday": "الثلاثاء",
    "Wednesday": "الأربعاء",
    "Thursday": "الخميس",
    "Friday": "الجمعة",
    "Saturday": "السبت",
    "Sunday": "الأحد"
}

# التحقق من وجود الملف أو إنشاء واحد جديد بأعمدة فارغة
if os.path.exists(DB_FILE):
    try:
        df_bookings = pd.read_csv(DB_FILE)
    except:
        df_bookings = pd.DataFrame(columns=["اسم الزبون", "التاريخ", "من الساعة", "إلى الساعة", "المبلغ المستلم"])
else:
    df_bookings = pd.DataFrame(columns=["اسم الزبون", "التاريخ", "من الساعة", "إلى الساعة", "المبلغ المستلم"])

# تقسيم التطبيق إلى تبويبين
tab1, tab2 = st.tabs(["📝 تسجيل حجز جديد", "📊 شاشة صاحب الشاليه"])

# --- القسم الأول: تسجيل الحجوزات ---
with tab1:
    st.header("إضافة حجز جديد")
    
    with st.form("booking_form", clear_on_submit=True):
        customer_name = st.text_input("اسم الزبون الفلاني:")
        booking_date = st.date_input("تاريخ الحجز:", min_value=datetime.today())
        
        col1, col2 = st.columns(2)
        with col1:
            time_from = st.time_input("من الساعة:", time(14, 0))
        with col2:
            time_to = st.time_input("إلى الساعة:", time(11, 0))
            
        amount = st.number_input("المبلغ المطلوب (بكذا من المال):", min_value=0, step=10)
        
        submit_button = st.form_submit_button("حفظ وتأكيد الحجز")
        
        if submit_button:
            if customer_name:
                # تجهيز السطر الجديد
                new_data = {
                    "اسم الزبون": customer_name,
                    "التاريخ": booking_date.strftime('%Y-%m-%d'),
                    "من الساعة": time_from.strftime('%H:%M'),
                    "إلى الساعة": time_to.strftime('%H:%M'),
                    "المبلغ المستلم": amount
                }
                # إضافة البيانات للملف وحفظها فوراً
                df_bookings = pd.concat([df_bookings, pd.DataFrame([new_data])], ignore_index=True)
                df_bookings.to_csv(DB_FILE, index=False)
                st.success(f"✅ تم تسجيل حجز {customer_name} بنجاح!")
                st.rerun()
            else:
                st.error("الرجاء إدخال اسم الزبون")

# --- القسم الثاني: شاشة عرض صاحب الشاليه ---
with tab2:
    st.header("🔍 الأيام والساعات المحجوزة")
    st.info("هذه الشاشة تظهر لصاحب الشاليه لمتابعة التواريخ والأوقات المحجوزة فقط.")
    
    if df_bookings.empty:
        st.warning("لا توجد حجوزات مسجلة حالياً.")
    else:
        # إنشاء نسخة من البيانات للعرض دون التأثير على الملف الأصلي
        df_owner_view = df_bookings.copy()
        
        # استخراج اسم اليوم بالإنجليزية ثم تحويله إلى العربية بناءً على التاريخ
        df_owner_view["اليوم"] = pd.to_datetime(df_owner_view["التاريخ"]).dt.day_name().map(DAYS_ARABIC)
        
        # ترتيب الأعمدة ليظهر عمود "اليوم" مباشرة بجانب عمود "التاريخ"
        df_owner_view = df_owner_view[["التاريخ", "اليوم", "من الساعة", "إلى الساعة"]]
        
        # عرض الجدول المفلتر لصاحب الشاليه
        st.dataframe(df_owner_view, use_container_width=True)
