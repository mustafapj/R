# qa_matcher.py - نظام المطابقة الذكي بين الأسئلة والإجابات

import re
from questions import QUESTION_CATEGORIES
from answers import get_random_answer

class QAMatcher:
    def __init__(self):
        self.setup_keyword_matching()
    
    def setup_keyword_matching(self):
        """إعداد كلمات مفتاحية للتعرف الذكي على الأسئلة"""
        self.keyword_categories = {
            # كلمات مفتاحية للتحيات
            "greetings": ["سلام", "هلو", "مرحبا", "شلون", "شخبار", "شكو", "شسوي"],
            
            # كلمات مفتاحية للمعلومات الشخصية
            "personal_info": ["اسم", "منين", "وين ساكن", "لقب", "عمر", "مواليد", "طالب", "مجال", "خريج"],
            
            # كلمات مفتاحية للهوايات
            "hobbies": ["تحب", "هوايات", "قراءة", "كتاب", "مسلسل", "أغاني", "ألعاب", "طبخ", "سيارة", "رياضة", "نادي"],
            
            # كلمات مفتاحية للمزاج
            "mood_personality": ["مزاج", "جو", "تمشي", "بحر", "جبال", "شتاء", "لون", "عطر", "لبس", "رومانسي"],
            
            # كلمات مفتاحية للعلاقات
            "relationships": ["أخوان", "أقرب", "اجتماعي", "تعارف", "تضحك", "تضوج", "زعل", "علاقات", "ناس", "هدايا"],
            
            # كلمات مفتاحية للأماكن
            "locations": ["وين", "بغداد", "ناصريه", "كوت", "ديوانيه", "بصره", "سماوه", "دهوك", "اربيل", "سليمانيه", "انبار", "كربلاء", "نجف", "كركوك", "سامره"],
            
            # كلمات مفتاحية للمشاعر
            "feelings_dreams": ["ضايج", "معودية", "تكره", "حيوانات", "أفضل يوم", "أسوأ يوم", "تخاف", "يتمنى", "أحلى مكان"]
        }
    
    def find_question_category(self, user_question):
        """البحث عن فئة السؤال باستخدام المطابقة الذكية"""
        user_question = user_question.lower()
        
        # 1. البحث المباشر في الفئات
        for category, questions in QUESTION_CATEGORIES.items():
            for question in questions:
                if self.similar_question(user_question, question.lower()):
                    return category
        
        # 2. البحث بالكلمات المفتاحية
        for category, keywords in self.keyword_categories.items():
            for keyword in keywords:
                if keyword in user_question:
                    return category
        
        # 3. إذا لم يتم العثور على مطابقة
        return None
    
    def similar_question(self, user_q, stored_q):
        """التحقق من تشابه الأسئلة"""
        # مطابقة مباشرة
        if user_q == stored_q:
            return True
        
        # مطابقة جزئية (إذا كان السؤال يحتوي على 70% من الكلمات)
        user_words = set(user_q.split())
        stored_words = set(stored_q.split())
        
        common_words = user_words.intersection(stored_words)
        similarity = len(common_words) / max(len(user_words), len(stored_words))
        
        return similarity >= 0.6
    
    def get_answer(self, user_question):
        """الحصول على الإجابة المناسبة للسؤال"""
        # البحث عن فئة السؤال
        category = self.find_question_category(user_question)
        
        if category:
            # إرجاع إجابة عشوائية من الفئة المناسبة
            return get_random_answer(category)
        else:
            # إذا لم يتم العثور على مطابقة
            return None

# إنشاء كائن المطابقة العالمي
qa_matcher = QAMatcher()