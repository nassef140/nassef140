# أضف هذا الجزء في نهاية الملف لعرض قائمة الأسهم الذهبية
if st.button("🚀 تشغيل رادار الاقتناص (مسح السوق)"):
    # قائمة عينة لأقوى أسهم البورصة المصرية
    egx_leaders = ["COMI", "FWRY", "ABUK", "EAST", "TMGH", "EKHO", "SWDY", "ORAS"]
    st.write("جاري فحص القادة وبصمات السيولة...")
    
    top_picks = []
    for s in egx_leaders:
        analysis = ai_bold_advisor_pro(s)
        if "error" not in analysis and analysis['confidence'] >= 70:
            top_picks.append(analysis)
            
    if top_picks:
        st.success(f"🎯 تم العثور على {len(top_picks)} فرص اقتناص عالية الثقة!")
        for pick in top_picks:
            st.markdown(f"✅ **{pick['symbol']}**: ثقة {pick['confidence']}% | المستهدف: {pick['target']:.2f}")
    else:
        st.warning("لا توجد فرص 'انفجار سعري' حالياً، السوق في مرحلة تجميع.")
