import sys
import random
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any
from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QListWidget,
    QComboBox,
    QTabWidget
)
from PyQt6.QtCore import Qt, QTimer

RESULTS_FILE = "results.json"
QUESTIONS_FILE = "questions.json"
TEACHERS_FILE = "teachers.json"
STUDENTS_FILE = "students.json"
TEACHER_PASSWORD = "Melomonik.21"

LEVEL_POINTS = {
    "Kolay": 1,
    "Orta": 2,
    "Zor": 3,
}

class Question:
    def __init__(self, text: str, choices: List[str], answer: str, level: str) -> None:
        self.text = text
        self.choices = choices
        self.answer = answer
        self.level = level

    def check_answer(self, answer: str) -> bool:
        return self.answer == answer

class Quiz:
    def __init__(self, questions: List[Question], exam_end_time: datetime | None = None) -> None:
        self.questions = questions
        self.score = 0
        self.index = 0
        self.answered = 0
        self.early_terminated = False
        self.points = 0
        self.max_points = 0
        self.level_stats = {
            "Kolay": {"correct": 0, "wrong": 0},
            "Orta": {"correct": 0, "wrong": 0},
            "Zor": {"correct": 0, "wrong": 0},
        }
        self.exam_end_time = exam_end_time

    def has_more_questions(self) -> bool:
        return self.index < len(self.questions)

    def time_over(self) -> bool:
        if self.exam_end_time is None:
            return False
        now = datetime.now()
        if now >= self.exam_end_time:
            self.early_terminated = True
            self.index = len(self.questions)
            return True
        return False

    def get_remaining_time(self) -> int:
        if self.exam_end_time is None:
            return -1
        remaining = self.exam_end_time - datetime.now()
        total = int(remaining.total_seconds())
        if total < 0:
            total = 0
        return total

    def get_current_question(self) -> "Question":
        return self.questions[self.index]

    def answer_current(self, choice_index: int) -> bool:
        if self.time_over():
            return False
        soru = self.get_current_question()
        soru_puan = LEVEL_POINTS.get(soru.level, 1)
        self.max_points += soru_puan
        secilen_cevap = soru.choices[choice_index]
        correct = soru.check_answer(secilen_cevap)
        if correct:
            self.score += 1
            self.points += soru_puan
            self.level_stats[soru.level]["correct"] += 1
        else:
            self.level_stats[soru.level]["wrong"] += 1
        self.index += 1
        self.answered += 1
        return correct

    def get_results(self):
        total_questions = len(self.questions)
        total_answered = self.answered
        correct = self.score
        wrong = total_answered - correct
        if total_answered > 0:
            percent = (correct / total_answered) * 100
        else:
            percent = 0
        if self.max_points > 0:
            point_percent = (self.points / self.max_points) * 100
        else:
            point_percent = 0
        level_label = get_level_label(point_percent)
        return (
            correct,
            wrong,
            percent,
            total_answered,
            total_questions,
            self.points,
            self.max_points,
            point_percent,
            level_label,
            self.level_stats,
        )

def get_level_label(point_percent: float) -> str:
    if point_percent < 40:
        return "Beginner"
    elif point_percent < 70:
        return "Intermediate"
    else:
        return "Advanced"

def analyze_weak_areas(level_stats: dict) -> str:
    infos = []
    for level, stats in level_stats.items():
        total = stats["correct"] + stats["wrong"]
        if total == 0:
            continue
        acc = (stats["correct"] / total) * 100
        infos.append((level, acc, total))
    if not infos:
        return "Bu sınavda soru cevaplanmadığı için seviye analizi yapılamadı."
    weakest = min(infos, key=lambda x: x[1])
    level_name, acc, total = weakest
    if level_name == "Kolay":
        extra = "Temel konuları biraz daha pekiştirmen iyi olur."
    elif level_name == "Orta":
        extra = "Orta seviye konularda (döngüler, fonksiyonlar, koleksiyonlar) biraz daha pratik yapabilirsin."
    else:
        extra = "İleri seviye konularda (OOP, generator, async, ileri fonksiyonlar) zorlanman normal; zamanla açılır."
    return (
        f"En çok zorlandığın seviye: {level_name} "
        f"(doğruluk: {acc:.2f}%, toplam {total} soru). {extra}"
    )

def build_study_suggestions(level_label: str, level_stats: dict):
    suggestions = []
    if level_label == "Beginner":
        suggestions.extend([
            "Temel veri tipleri: int, float, str, bool",
            "Karşılaştırma ve mantıksal operatörler",
            "Koşul ifadeleri: if / elif / else",
            "Temel döngüler: for ve while",
            "Liste ve sözlük (list, dict) temelleri",
        ])
    elif level_label == "Intermediate":
        suggestions.extend([
            "Fonksiyon yazma ve parametreler (varsayılan parametreler dahil)",
            "List, dict, set ve tuple ile pratik",
            "List comprehension ve temel lambda kullanımı",
            "try / except ile hata yönetimi",
            "Dosya okuma/yazma (file I/O) ve with kullanımı",
        ])
    else:
        suggestions.extend([
            "Nesne yönelimli programlama: class, __init__, miras (inheritance)",
            "Generator ve iterator mantığı, yield kullanımı",
            "Decorators ve ileri fonksiyonel programlama",
            "Asenkron programlama: async / await",
            "Sanal ortam (virtualenv) ve paket yönetimi (pip)",
        ])
    infos = []
    for level, stats in level_stats.items():
        total = stats["correct"] + stats["wrong"]
        if total == 0:
            continue
        acc = (stats["correct"] / total) * 100
        infos.append((level, acc, total))
    if infos:
        weakest = min(infos, key=lambda x: x[1])
        level_name, acc, total = weakest
        if level_name == "Kolay":
            suggestions.extend([
                "Değişken tanımlama ve isimlendirme kuralları",
                "Temel aritmetik işlemler ve öncelik kuralları",
                "Basit döngü örnekleri ile pratik",
            ])
        elif level_name == "Orta":
            suggestions.extend([
                "List/dict işlemleri (append, pop, insert, keys vs.)",
                "range, enumerate, map, filter gibi fonksiyonları tekrar et",
                "String dilimleme ve formatlama (format, f-string)",
            ])
        else:
            suggestions.extend([
                "Decorator ve context manager örnekleri incele",
                "PEP 8 stil rehberini gözden geçir",
                "Gerçek projelerde OOP tasarım örneklerine bak",
            ])
    seen = set()
    unique_suggestions = []
    for s in suggestions:
        if s not in seen:
            seen.add(s)
            unique_suggestions.append(s)
    return unique_suggestions

def load_results() -> Dict[str, Any]:
    if not os.path.exists(RESULTS_FILE):
        return {}
    try:
        with open(RESULTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_results(data: Dict[str, Any]) -> None:
    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_custom_questions() -> Dict[str, list]:
    if not os.path.exists(QUESTIONS_FILE):
        return {"easy": [], "medium": [], "hard": []}
    try:
        with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {
            "easy": data.get("easy", []),
            "medium": data.get("medium", []),
            "hard": data.get("hard", []),
        }
    except Exception:
        return {"easy": [], "medium": [], "hard": []}

def save_custom_questions(data: Dict[str, list]) -> None:
    with open(QUESTIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def save_teachers(data: list) -> None:
    with open(TEACHERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_teachers() -> list:
    if not os.path.exists(TEACHERS_FILE):
        data = [{"name": "Admin", "password": TEACHER_PASSWORD}]
        save_teachers(data)
        return data
    try:
        with open(TEACHERS_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except Exception:
        data = [{"name": "Admin", "password": TEACHER_PASSWORD}]
        save_teachers(data)
        return data
    normalized = []
    if isinstance(raw, list):
        for item in raw:
            if isinstance(item, dict):
                name = item.get("name", "")
                pwd = item.get("password", TEACHER_PASSWORD)
                if name:
                    normalized.append({"name": name, "password": pwd})
            elif isinstance(item, str):
                normalized.append({"name": item, "password": TEACHER_PASSWORD})
    else:
        normalized = [{"name": "Admin", "password": TEACHER_PASSWORD}]
    save_teachers(normalized)
    return normalized

def save_students(data: list) -> None:
    with open(STUDENTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_students() -> list:
    if not os.path.exists(STUDENTS_FILE):
        return []
    try:
        with open(STUDENTS_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except Exception:
        return []
    students = []
    if isinstance(raw, list):
        for item in raw:
            if isinstance(item, dict):
                name = item.get("name", "")
                pwd = item.get("password", "")
                if name:
                    students.append({"name": name, "password": pwd})
            elif isinstance(item, str):
                students.append({"name": item, "password": ""})
    save_students(students)
    return students

def build_question_bank():
    easy = [
        Question("Python dosya uzantısı nedir?",
                 [".pt", ".py", ".python", ".pyt"], ".py", "Kolay"),
        Question("Python'da ekrana yazdırmak için hangi fonksiyon kullanılır?",
                 ["echo()", "print()", "write()", "out()"], "print()", "Kolay"),
        Question("Python'da bir satır yorum nasıl başlar?",
                 ["//", "#", "/*", "<!--"], "#", "Kolay"),
        Question("Aşağıdakilerden hangisi geçerli bir değişken adıdır?",
                 ["1sayi", "sayi_1", "sayi-1", "sayi 1"], "sayi_1", "Kolay"),
        Question("type(10) ifadesinin sonucu hangi veri tipidir?",
                 ["int", "float", "str", "bool"], "int", "Kolay"),
        Question("type(3.14) ifadesinin sonucu hangi veri tipidir?",
                 ["int", "float", "str", "bool"], "float", "Kolay"),
        Question("'Merhaba' hangi veri tipidir?",
                 ["int", "float", "str", "bool"], "str", "Kolay"),
        Question("True ve False hangi veri tipine aittir?",
                 ["int", "str", "bool", "float"], "bool", "Kolay"),
        Question("Aşağıdakilerden hangisi liste tanımıdır?",
                 ["(1, 2, 3)", "{1, 2, 3}", "[1, 2, 3]", "\"1,2,3\""],
                 "[1, 2, 3]", "Kolay"),
        Question("len([10, 20, 30]) sonucu nedir?",
                 ["2", "3", "4", "Hata verir"], "3", "Kolay"),
        Question("Python'da atama operatörü hangisidir?",
                 ["==", "=", ":=", "=>"], "=", "Kolay"),
        Question("5 + 3 * 2 işleminin sonucu nedir?",
                 ["16", "11", "13", "10"], "11", "Kolay"),
        Question("a = 10; b = 3; a % b sonucu nedir?",
                 ["0", "1", "3", "Hata verir"], "1", "Kolay"),
        Question("input() fonksiyonu ne yapar?",
                 ["Ekrana yazar", "Klavye girişini okur", "Dosya açar", "Programı sonlandırır"],
                 "Klavye girişini okur", "Kolay"),
        Question("a = 'Python'; a[0] nedir?",
                 ["'P'", "'y'", "'n'", "Hata verir"], "'P'", "Kolay"),
        Question("a = [1, 2, 3]; a[1] nedir?",
                 ["1", "2", "3", "Hata verir"], "2", "Kolay"),
        Question("Aşağıdakilerden hangisi tuple tanımıdır?",
                 ["[1, 2, 3]", "(1, 2, 3)", "{1, 2, 3}", "\"1,2,3\""],
                 "(1, 2, 3)", "Kolay"),
        Question("Aşağıdakilerden hangisi sözlük (dict) tanımıdır?",
                 ["[1, 2, 3]", "(1, 2, 3)", "{\"ad\": \"Ali\"}", "{1, 2, 3}"],
                 "{\"ad\": \"Ali\"}", "Kolay"),
        Question("3 == 3 ifadesinin sonucu nedir?",
                 ["True", "False", "3", "Hata verir"], "True", "Kolay"),
        Question("3 != 5 ifadesinin sonucu nedir?",
                 ["True", "False", "5", "Hata verir"], "True", "Kolay"),
        Question("not True ifadesi ne döndürür?",
                 ["True", "False", "None", "Hata verir"], "False", "Kolay"),
        Question("a = 5; a += 2 sonrası a nedir?",
                 ["5", "7", "2", "Hata verir"], "7", "Kolay"),
        Question("Python'da 've' anlamına gelen mantıksal operatör hangisidir?",
                 ["and", "or", "not", "&"], "and", "Kolay"),
        Question("Python'da 'veya' anlamına gelen mantıksal operatör hangisidir?",
                 ["and", "or", "not", "|"], "or", "Kolay"),
        Question("Boş liste nasıl tanımlanır?",
                 ["()", "{}", "[]", "''"], "[]", "Kolay"),
        Question("Boş string nasıl tanımlanır?",
                 ["[]", "{}", "''", "None"], "''", "Kolay"),
        Question("None neyi ifade eder?",
                 ["0", "Boş string", "Hiçlik/değer yok", "False"],
                 "Hiçlik/değer yok", "Kolay"),
        Question("Python'da bloklar nasıl ayrılır?",
                 ["Parantez ile", "Virgül ile", "Girinti (indent) ile", "Noktalı virgül ile"],
                 "Girinti (indent) ile", "Kolay"),
        Question("Aşağıdakilerden hangisi Python anahtar kelimesidir?",
                 ["number", "value", "if", "string"], "if", "Kolay"),
        Question("Hangi ifade sözlükteki anahtar sayısını verir?",
                 ["len(dict)", "size(dict)", "count(dict)", "length(dict)"],
                 "len(dict)", "Kolay"),
    ]

    medium = [
        Question("a = 'Python'; a[1:4] ifadesinin sonucu nedir?",
                 ["'Pyt'", "'yth'", "'ytho'", "'Pyt'"], "'yth'", "Orta"),
        Question("range(1, 4) hangi değerleri üretir?",
                 ["1, 2, 3", "1, 2, 3, 4", "0, 1, 2", "2, 3, 4"], "1, 2, 3", "Orta"),
        Question("for i in range(3): print(i) çıktısı nedir?",
                 ["0 1 2", "1 2 3", "0 1 2 3", "1 2"], "0 1 2", "Orta"),
        Question("while döngüsü için doğru ifade hangisidir?",
                 ["Koşul sağlandığı sürece döner", "Sadece bir kez çalışır",
                  "Her zaman sonsuz döngüdür", "For döngüsüyle aynıdır"],
                 "Koşul sağlandığı sürece döner", "Orta"),
        Question("break ifadesi ne yapar?",
                 ["Döngüyü sonlandırır", "Döngüyü atlar", "Değişkeni siler", "Fonksiyonu bitirir"],
                 "Döngüyü sonlandırır", "Orta"),
        Question("continue ifadesi ne yapar?",
                 ["Döngüyü tamamen bitirir", "O turu atlayıp döngüye devam eder",
                  "Hata fırlatır", "Fonksiyonu sonlandırır"],
                 "O turu atlayıp döngüye devam eder", "Orta"),
        Question("def fonksiyon(): tanımında hangi anahtar kelime kullanılır?",
                 ["function", "def", "fun", "lambda"], "def", "Orta"),
        Question("return ifadesi ne yapar?",
                 ["Fonksiyondan değer döndürür", "Döngüyü sonlandırır",
                  "Değişken tanımlar", "Modül yükler"],
                 "Fonksiyondan değer döndürür", "Orta"),
        Question("a = [1, 2, 3]; a.append(4) sonrası a nedir?",
                 ["[1, 2, 3]", "[1, 2, 3, 4]", "[4, 1, 2, 3]", "[1, 2, 4]"],
                 "[1, 2, 3, 4]", "Orta"),
        Question("a = [1, 2, 3]; a.insert(1, 10) sonrası a nedir?",
                 ["[1, 10, 2, 3]", "[10, 1, 2, 3]", "[1, 2, 10, 3]", "[1, 2, 3, 10]"],
                 "[1, 10, 2, 3]", "Orta"),
        Question("a = [1, 2, 3]; a.pop() sonrası a nedir?",
                 ["[1, 2]", "[2, 3]", "[1, 3]", "[]"], "[1, 2]", "Orta"),
        Question("a = {\"ad\": \"Ali\", \"yas\": 20}; a[\"ad\"] nedir?",
                 ["\"Ali\"", "20", "\"ad\"", "Hata verir"], "\"Ali\"", "Orta"),
        Question("dict.keys() ne döndürür?",
                 ["Anahtarları", "Değerleri", "Hem anahtar hem değerleri", "Uzunluğu"],
                 "Anahtarları", "Orta"),
        Question("set veri tipinin özelliği nedir?",
                 ["Sıralıdır", "Tekrar eden eleman tutmaz", "İndekslenebilir", "Sadece int tutar"],
                 "Tekrar eden eleman tutmaz", "Orta"),
        Question("a = [1, 2, 3]; b = a; b.append(4) sonrası a nedir?",
                 ["[1, 2, 3]", "[1, 2, 3, 4]", "[4, 1, 2, 3]", "Hata verir"],
                 "[1, 2, 3, 4]", "Orta"),
        Question("a = [1, 2, 3]; b = a.copy(); b.append(4) sonrası a nedir?",
                 ["[1, 2, 3]", "[1, 2, 3, 4]", "[4, 1, 2, 3]", "Hata verir"],
                 "[1, 2, 3]", "Orta"),
        Question("Fonksiyon parametresinde varsayılan değer nasıl verilir?",
                 ["def f(a, b: 0)", "def f(a, b = 0)", "def f(a, b == 0)", "def f(a, b := 0)"],
                 "def f(a, b = 0)", "Orta"),
        Question("try/except yapısı ne için kullanılır?",
                 ["Döngü yazmak için", "Koşul yazmak için", "Hata yakalamak için", "Fonksiyon tanımlamak için"],
                 "Hata yakalamak için", "Orta"),
        Question("open('dosya.txt', 'r') ne yapar?",
                 ["Dosyayı okuma modunda açar", "Dosyayı yazma modunda açar",
                  "Dosyayı siler", "Hiçbir şey yapmaz"],
                 "Dosyayı okuma modunda açar", "Orta"),
        Question("with open('dosya.txt', 'r') as f: yapısı ne sağlar?",
                 ["Otomatik dosya kapatma", "Dosyanın kopyasını oluşturma",
                  "Dosyayı şifreleme", "Hiçbir şey"],
                 "Otomatik dosya kapatma", "Orta"),
        Question("modül içe aktarmak için hangi ifade kullanılır?",
                 ["include math", "using math", "import math", "require math"],
                 "import math", "Orta"),
        Question("Aşağıdakilerden hangisi gömülü bir Python fonksiyonudur?",
                 ["len()", "size()", "length()", "count()"],
                 "len()", "Orta"),
        Question("map(f, liste) ifadesi ne döndürür?",
                 ["Liste", "Iterator", "Set", "Sözlük"],
                 "Iterator", "Orta"),
        Question("filter(f, liste) ne yapar?",
                 ["Listeyi sıralar", "Listeyi ters çevirir", "Şarta uyanları süzer", "Listeyi kopyalar"],
                 "Şarta uyanları süzer", "Orta"),
        Question("sorted([3, 1, 2]) sonucu nedir?",
                 ["[3, 2, 1]", "[1, 2, 3]", "[2, 1, 3]", "Hata verir"],
                 "[1, 2, 3]", "Orta"),
        Question("join() hangi veri tipiyle kullanılır?",
                 ["int", "list of int", "list of str", "dict"],
                 "list of str", "Orta"),
        Question("'-'.join(['a', 'b', 'c']) sonucu nedir?",
                 ["'abc'", "'a-b-c'", "'a-bc'", "'ab-c'"],
                 "'a-b-c'", "Orta"),
        Question("formatlama için doğru ifade hangisidir?",
                 ["'Merhaba {}'.format('Ali')", "'Merhaba'.format('Ali')",
                  "format('Merhaba', 'Ali')", "'Merhaba' + format('Ali')"],
                 "'Merhaba {}'.format('Ali')", "Orta"),
        Question("f-string kullanımına örnek hangisidir?",
                 ["'Merhaba {isim}'", "f'Merhaba {isim}'",
                  "f('Merhaba {isim}')", "format('Merhaba {isim}')"],
                 "f'Merhaba {isim}'", "Orta"),
        Question(
            "enumerate(liste) ne sağlar?",
            ["Sadece indeksleri verir", "Sadece değerleri verir",
             "Hem indeks hem değeri verir", "Hiçbir şey"],
            "Hem indeks hem değeri verir", "Orta"),
    ]

    hard = [
        Question("[x for x in range(5) if x % 2 == 0] sonucu nedir?",
                 ["[0, 1, 2, 3, 4]", "[1, 3]", "[0, 2, 4]", "[2, 4]"],
                 "[0, 2, 4]", "Zor"),
        Question("lambda x: x * 2 ifadesi neyi temsil eder?",
                 ["Sınıf", "Anonim fonksiyon", "Modül", "Paket"],
                 "Anonim fonksiyon", "Zor"),
        Question("def f(*args) ifadesinde *args ne işe yarar?",
                 ["İstenilen sayıda konumsal argüman alır",
                  "İstenilen sayıda anahtar argüman alır",
                  "Hiç argüman almaz", "Sadece bir argüman alır"],
                 "İstenilen sayıda konumsal argüman alır", "Zor"),
        Question("def f(**kwargs) ifadesi ne işe yarar?",
                 ["İstenilen sayıda konumsal argüman alır",
                  "İstenilen sayıda anahtar argüman alır",
                  "Liste döndürür", "Set döndürür"],
                 "İstenilen sayıda anahtar argüman alır", "Zor"),
        Question("Generator fonksiyon oluşturmak için hangi anahtar kelime kullanılır?",
                 ["yield", "return", "generate", "async"],
                 "yield", "Zor"),
        Question("class A:\n    def __init__(self):\n        self.x = 10\n__init__ ne işe yarar?",
                 ["Modül yükler", "Yapıcı metoddur, nesneyi başlatır",
                  "Sınıfı siler", "Hiçbir özel anlamı yoktur"],
                 "Yapıcı metoddur, nesneyi başlatır", "Zor"),
        Question("Miras alma (inheritance) için hangi söz dizimi kullanılır?",
                 ["class B -> A:", "class B(A):", "class B:A", "class B = A:"],
                 "class B(A):", "Zor"),
        Question("raise ValueError('hata') ne yapar?",
                 ["Hata mesajını ekrana yazar", "ValueError istisnası fırlatır",
                  "Programı kapatır", "Hiçbir şey"],
                 "ValueError istisnası fırlatır", "Zor"),
        Question("try/except/finally yapısında finally ne zaman çalışır?",
                 ["Sadece hata olunca", "Sadece hata olmayınca",
                  "Her durumda", "Hiç çalışmaz"],
                 "Her durumda", "Zor"),
        Question("Decorator ne için kullanılır?",
                 ["Fonksiyonu silmek için", "Fonksiyona ekstra davranış eklemek için",
                  "Modül oluşturmak için", "Değişken tanımlamak için"],
                 "Fonksiyona ekstra davranış eklemek için", "Zor"),
        Question("@decorator ifadesi neyi temsil eder?",
                 ["Sınıf tanımı", "Decorator uygulaması",
                  "Modül importu", "Generator"],
                 "Decorator uygulaması", "Zor"),
        Question("__str__ metodu ne zaman çağrılır?",
                 ["Nesne oluşturulurken", "Nesne silinirken",
                  "str(nesne) veya print(nesne) çağrıldığında", "Hiç çağrılmaz"],
                 "str(nesne) veya print(nesne) çağrıldığında", "Zor"),
        Question("__len__ metodu ne işe yarar?",
                 ["Toplama yapar", "Uzunluk döndürür", "Karşılaştırma yapar", "Hata fırlatır"],
                 "Uzunluk döndürür", "Zor"),
        Question("İteratör protokolü hangi metodları gerektirir?",
                 ["__iter__ ve __next__", "__add__ ve __sub__",
                  "__init__ ve __del__", "__get__ ve __set__"],
                 "__iter__ ve __next__", "Zor"),
        Question("list(map(lambda x: x*2, [1, 2, 3])) sonucu nedir?",
                 ["[1, 2, 3]", "[2, 4, 6]", "[0, 1, 2]", "[1, 4, 9]"],
                 "[2, 4, 6]", "Zor"),
        Question("list(filter(lambda x: x % 2 == 0, [1, 2, 3, 4])) sonucu nedir?",
                 ["[1, 3]", "[2, 4]", "[1, 2, 3, 4]", "[]"],
                 "[2, 4]", "Zor"),
        Question("list comprehension ile kareler listesi nasıl oluşturulur?",
                 ["[x**2 for x in liste]", "[x for x**2 in liste]",
                  "x**2 in liste", "map(x**2, liste)"],
                 "[x**2 for x in liste]", "Zor"),
        Question("from modul import * ifadesinin sakıncası nedir?",
                 ["Hiçbir sakıncası yoktur", "İsim çakışmalarına yol açabilir",
                  "Modülü siler", "Performansı her zaman düşürür"],
                 "İsim çakışmalarına yol açabilir", "Zor"),
        Question("virtual environment (sanal ortam) ne için kullanılır?",
                 ["İşletim sistemini değiştirmek için",
                  "Projeye özel bağımlılık yönetimi için",
                  "Dosya silmek için", "Python sürümünü silmek için"],
                 "Projeye özel bağımlılık yönetimi için", "Zor"),
        Question("JSON verisi Python'da hangi tipe dönüştürülür?",
                 ["Her zaman list", "Her zaman dict",
                  "JSON içeriğine göre list/dict", "Her zaman str"],
                 "JSON içeriğine göre list/dict", "Zor"),
        Question("open('dosya.txt', 'wb') modu ne yapar?",
                 ["Metin okur", "Metin yazar", "Binary yazar", "Binary okur"],
                 "Binary yazar", "Zor"),
        Question("async/await yapısı ne için kullanılır?",
                 ["Çoklu miras için", "Asenkron programlama için",
                  "Dosya yönetimi için", "Dekorator tanımı için"],
                 "Asenkron programlama için", "Zor"),
        Question("list(set([1, 1, 2, 2, 3])) sonucu nedir?",
                 ["[1, 1, 2, 2, 3]", "[1, 2, 3]", "[3, 2, 1]", "Sırasız bir liste, tekrar yok"],
                 "Sırasız bir liste, tekrar yok", "Zor"),
        Question("a = {1, 2, 3}; b = {3, 4, 5}; a & b nedir?",
                 ["{1, 2, 3, 4, 5}", "{1, 2}", "{3}", "Boş küme"],
                 "{3}", "Zor"),
        Question("a = {1, 2, 3}; b = {3, 4, 5}; a | b nedir?",
                 ["{1, 2, 3, 4, 5}", "{1, 2}", "{3}", "Boş küme"],
                 "{1, 2, 3, 4, 5}", "Zor"),
        Question("context manager ne sağlar?",
                 ["Bellek yönetimi yapar",
                  "Kaynağın güvenli açılıp kapatılmasını sağlar",
                  "Değişkenleri siler", "Sadece dosya okur"],
                 "Kaynağın güvenli açılıp kapatılmasını sağlar", "Zor"),
        Question("__name__ == '__main__' kontrolü ne için kullanılır?",
                 ["Modülü silmek için",
                  "Dosya direkt çalıştırıldığında kod bloğunu çalıştırmak için",
                  "Her zaman import etmek için", "Hiçbir şey için"],
                 "Dosya direkt çalıştırıldığında kod bloğunu çalıştırmak için", "Zor"),
        Question("logging modülü ne için kullanılır?",
                 ["Rastgele sayı üretmek için",
                  "Loglama ve kayıt tutmak için",
                  "Şifreleme için", "Dosya silmek için"],
                 "Loglama ve kayıt tutmak için", "Zor"),
        Question("pip ne için kullanılır?",
                 ["Python sürümünü güncellemek için",
                  "Python paketlerini yönetmek için",
                  "İşletim sistemi kurmak için", "Veritabanı yönetmek için"],
                 "Python paketlerini yönetmek için", "Zor"),
        Question("PEP 8 neyi ifade eder?",
                 ["Standart kütüphane", "Python stil rehberi",
                  "Paket yöneticisi", "Veritabanı arayüzü"],
                 "Python stil rehberi", "Zor"),
    ]

    extra = load_custom_questions()
    for qd in extra["easy"]:
        easy.append(Question(qd["text"], qd["choices"], qd["answer"], "Kolay"))
    for qd in extra["medium"]:
        medium.append(Question(qd["text"], qd["choices"], qd["answer"], "Orta"))
    for qd in extra["hard"]:
        hard.append(Question(qd["text"], qd["choices"], qd["answer"], "Zor"))
    return easy, medium, hard

def build_exam_questions(easy, medium, hard, per_level=5):
    if len(easy) < per_level or len(medium) < per_level or len(hard) < per_level:
        raise ValueError("Her seviye için yeterli sayıda soru yok.")
    selected_easy = random.sample(easy, per_level)
    selected_medium = random.sample(medium, per_level)
    selected_hard = random.sample(hard, per_level)
    questions = selected_easy + selected_medium + selected_hard
    random.shuffle(questions)
    return questions

def build_teacher_general_report(results: Dict[str, Any]) -> str:
    if not results:
        return "Kayıtlı hiçbir öğrenci bulunamadı."
    lines = []
    lines.append("ÖĞRETMEN PANELİ - GENEL RAPOR")
    lines.append("")
    students_stats = []
    for name, records in results.items():
        if not records:
            continue
        total_exams = len(records)
        last_exam = records[-1]
        best_points = max((r.get("points", 0) for r in records), default=0)
        avg_percent = sum(r.get("percent", 0) for r in records) / total_exams
        last_date = last_exam.get("datetime", "?")
        last_level = last_exam.get("level_label", "?")
        students_stats.append({
            "name": name,
            "total_exams": total_exams,
            "last_date": last_date,
            "best_points": best_points,
            "avg_percent": avg_percent,
            "last_level": last_level,
        })
    lines.append("[Öğrenci Bazlı Özet]")
    lines.append("-" * 60)
    for s in students_stats:
        lines.append(
            f"Öğrenci : {s['name']}\n"
            f"  Toplam Sınav   : {s['total_exams']}\n"
            f"  Son Sınav      : {s['last_date']}\n"
            f"  En Yüksek Puan : {s['best_points']}\n"
            f"  Ortalama Yüzde : {s['avg_percent']:.2f}%\n"
            f"  Son Seviye     : {s['last_level']}\n"
            + "-" * 60
        )
    by_best_points = sorted(
        students_stats, key=lambda x: x["best_points"], reverse=True
    )
    by_avg_percent = sorted(
        students_stats, key=lambda x: x["avg_percent"], reverse=True
    )
    by_total_exams = sorted(
        students_stats, key=lambda x: x["total_exams"], reverse=True
    )
    lines.append("")
    lines.append("[En Yüksek Puan Sıralaması]")
    lines.append("-" * 60)
    for i, s in enumerate(by_best_points, start=1):
        lines.append(f"{i:>2}) {s['name']:<20}  En Yüksek Puan: {s['best_points']}  | Son Seviye: {s['last_level']}")
    lines.append("")
    lines.append("[Ortalama Başarı Yüzdesi Sıralaması]")
    lines.append("-" * 60)
    for i, s in enumerate(by_avg_percent, start=1):
        lines.append(f"{i:>2}) {s['name']:<20}  Ortalama: {s['avg_percent']:.2f}%  | Son Seviye: {s['last_level']}")
    lines.append("")
    lines.append("[En Çok Sınava Giren Öğrenciler]")
    lines.append("-" * 60)
    for i, s in enumerate(by_total_exams, start=1):
        lines.append(f"{i:>2}) {s['name']:<20}  Sınav Sayısı: {s['total_exams']}  | Son Seviye: {s['last_level']}")
    level_counts = {"Beginner": 0, "Intermediate": 0, "Advanced": 0, "Diğer": 0}
    for s in students_stats:
        lvl = s["last_level"]
        if lvl in level_counts:
            level_counts[lvl] += 1
        else:
            level_counts["Diğer"] += 1
    lines.append("")
    lines.append("[Son Sınavlara Göre Seviye Dağılımı]")
    lines.append("-" * 60)
    for lvl, count in level_counts.items():
        lines.append(f"{lvl:<12}: {count} öğrenci")
    return "\n".join(lines)

def build_teacher_student_detail_text(results: Dict[str, Any], name: str) -> str:
    records = results.get(name, [])
    if not records:
        return "Bu öğrencinin kayıtlı sınavı yok."
    lines = []
    lines.append(f"ÖĞRENCİ DETAY RAPORU - {name}")
    lines.append("=" * 50)
    for i, rec in enumerate(records, start=1):
        lines.append(f"\n--- Sınav #{i} ---")
        lines.append(f"Tarih          : {rec.get('datetime', '?')}")
        lines.append(f"Doğru / Yanlış : {rec.get('correct', '?')} / {rec.get('wrong', '?')}")
        lines.append(f"Cevaplanan     : {rec.get('answered', '?')} / {rec.get('total_questions', '?')}")
        lines.append(f"Yüzde          : {rec.get('percent', 0):.2f}%")
        if "points" in rec and "max_points" in rec:
            lines.append(
                f"Puan           : {rec['points']}/{rec['max_points']} "
                f"({rec.get('point_percent', 0):.2f}%)"
            )
        if "level_label" in rec:
            lines.append(f"Seviye etiketi : {rec['level_label']}")
        if rec.get("early_terminated"):
            lines.append("Not            : Bu sınav erken sonlandırılmış.")
        teacher_name = rec.get("teacher", None)
        if teacher_name:
            lines.append(f"Öğretmen       : {teacher_name}")
        lines.append("-" * 50)
    return "\n".join(lines)

class ModeWindow(QWidget):
    def __init__(self, results: Dict[str, Any], teachers: list):
        super().__init__()
        self.results = results
        self.teachers = teachers
        self.setWindowTitle("Python Sınav Sistemi")
        self.setFixedSize(650, 500)
        self.setStyleSheet(
            "QWidget {"
            "  background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1,"
            "    stop:0 #020617, stop:1 #0b1120);"
            "  color: white;"
            "}"
            "QPushButton {"
            "  background-color: #2563eb;"
            "  color: white;"
            "  border-radius: 12px;"
            "  padding: 10px;"
            "  font-size: 16px;"
            "  font-weight: 500;"
            "}"
            "QPushButton:hover {"
            "  background-color: #3b82f6;"
            "}"
            "QLabel {"
            "  font-size: 14px;"
            "}"
        )
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 30, 40, 30)
        main_layout.setSpacing(15)
        header_layout = QVBoxLayout()
        header_layout.setSpacing(4)
        logo_label = QLabel("🐍")
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_label.setStyleSheet("font-size: 44px;")
        header_layout.addWidget(logo_label)
        title_label = QLabel("Python Sınav Sistemi")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        header_layout.addWidget(title_label)
        subtitle = QLabel("Seviyene göre Python testleri, detaylı analiz ve öğretmen paneli")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #9ca3af; font-size: 13px;")
        subtitle.setWordWrap(True)
        header_layout.addWidget(subtitle)
        main_layout.addLayout(header_layout)
        main_layout.addStretch()
        card = QWidget()
        card.setStyleSheet(
            "QWidget {"
            "  background-color: rgba(15, 23, 42, 0.9);"
            "  border-radius: 18px;"
            "  border: 1px solid #1d4ed8;"
            "}"
        )
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 22, 24, 22)
        card_layout.setSpacing(16)
        card_title = QLabel("Giriş Modu Seçimi")
        card_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        card_layout.addWidget(card_title)
        card_desc = QLabel("Öğrenci olarak sınava girebilir veya öğretmen paneline erişebilirsin.")
        card_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_desc.setWordWrap(True)
        card_desc.setStyleSheet("color: #9ca3af; font-size: 13px;")
        card_layout.addWidget(card_desc)
        card_layout.addSpacing(8)
        btn_col_layout = QVBoxLayout()
        btn_col_layout.setSpacing(10)
        self.student_btn = QPushButton("Öğrenci Girişi")
        self.teacher_btn = QPushButton("Öğretmen Girişi")
        self.student_btn.setMinimumHeight(42)
        self.teacher_btn.setMinimumHeight(42)
        self.student_btn.clicked.connect(self.open_student_login)
        self.teacher_btn.clicked.connect(self.open_teacher_login)
        btn_col_layout.addWidget(self.student_btn)
        btn_col_layout.addWidget(self.teacher_btn)
        card_layout.addLayout(btn_col_layout)
        hint_label = QLabel("İpucu: Öğrenciler önce öğretmenini seçerek sınava girer.")
        hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint_label.setStyleSheet("color: #6b7280; font-size: 12px; margin-top: 4px;")
        card_layout.addWidget(hint_label)
        main_layout.addWidget(card)
        main_layout.addStretch()
        self.register_label = QLabel("<a style='color:#60a5fa; text-decoration:none;' href='#'>Öğretmen kaydı oluştur</a>")
        self.register_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.register_label.setTextFormat(Qt.TextFormat.RichText)
        self.register_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        self.register_label.setOpenExternalLinks(False)
        self.register_label.linkActivated.connect(self.open_teacher_register)
        self.register_label.setStyleSheet("font-size: 13px;")
        main_layout.addWidget(self.register_label)

    def open_student_login(self):
        self.login_window = LoginWindow("student", self.results, self.teachers)
        self.login_window.show()
        self.close()

    def open_teacher_login(self):
        self.login_window = LoginWindow("teacher", self.results, self.teachers)
        self.login_window.show()
        self.close()

    def open_teacher_register(self):
        self.register_window = TeacherRegisterWindow(self.results, self.teachers)
        self.register_window.show()
        self.close()

class TeacherRegisterWindow(QWidget):
    def __init__(self, results: Dict[str, Any], teachers: list):
        super().__init__()
        self.results = results
        self.teachers = teachers
        self.setWindowTitle("Öğretmen Kaydı")
        self.setFixedSize(480, 320)
        self.setStyleSheet(
            "QWidget {background-color: #020617; color: white;}"
            "QPushButton {background-color: #2563eb; color: white; border-radius: 10px; padding: 8px; font-size: 14px;}"
            "QPushButton:hover {background-color: #3b82f6;}"
            "QLineEdit {background-color: #020617; color: white; padding: 8px; border-radius: 8px; border: 1px solid #1d4ed8;}"
            "QLabel {font-size: 14px;}"
        )
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        title = QLabel("Yeni Öğretmen Kaydı")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)
        self.name_label = QLabel("Öğretmen Ad Soyad:")
        self.name_edit = QLineEdit()
        layout.addWidget(self.name_label)
        layout.addWidget(self.name_edit)
        self.password_label = QLabel("Şifre:")
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.password_label)
        layout.addWidget(self.password_edit)
        btn_layout = QHBoxLayout()
        self.back_btn = QPushButton("Geri")
        self.save_btn = QPushButton("Kaydı Oluştur")
        self.back_btn.clicked.connect(self.go_back)
        self.save_btn.clicked.connect(self.save_teacher)
        btn_layout.addWidget(self.back_btn)
        btn_layout.addWidget(self.save_btn)
        layout.addLayout(btn_layout)

    def go_back(self):
        teachers = load_teachers()
        self.mode_window = ModeWindow(self.results, teachers)
        self.mode_window.show()
        self.close()

    def save_teacher(self):
        name = self.name_edit.text().strip()
        pwd = self.password_edit.text().strip()
        if not name or not pwd:
            QMessageBox.warning(self, "Hata", "İsim ve şifre boş bırakılamaz.")
            return
        teachers = load_teachers()
        for t in teachers:
            if t.get("name", "").lower() == name.lower():
                QMessageBox.warning(self, "Hata", "Bu isimde bir öğretmen zaten mevcut.")
                return
        teachers.append({"name": name, "password": pwd})
        save_teachers(teachers)
        QMessageBox.information(self, "Başarılı", "Öğretmen kaydı oluşturuldu.")
        self.go_back()

class PasswordChangeWindow(QWidget):
    def __init__(self, mode: str, name: str):
        super().__init__()
        self.mode = mode
        self.name = name.strip()

        if self.mode == "teacher":
            self.setWindowTitle("Öğretmen Şifre Değiştir")
        else:
            self.setWindowTitle("Öğrenci Şifre Değiştir")

        # YÜKSEKLİĞİ ARTIRDIM (260 → 310)
        self.setFixedSize(420, 310)

        self.setStyleSheet(
            "QWidget {background-color: #020617; color: white;}"
            "QPushButton {background-color: #2563eb; color: white; "
            "border-radius: 10px; padding: 8px; font-size: 14px;}"
            "QPushButton:hover {background-color: #3b82f6;}"
            "QLineEdit {background-color: #020617; color: white; padding: 8px; "
            "border-radius: 8px; border: 1px solid #1d4ed8;}"
            "QLabel {font-size: 14px;}"
        )

        layout = QVBoxLayout(self)
        # Biraz daha sıkı ama taşma olmayacak şekilde ayarladım
        layout.setContentsMargins(24, 16, 24, 16)
        layout.setSpacing(10)

        title = QLabel(self.windowTitle())
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)

        if self.mode == "teacher":
            old_label_text = "Eski Şifre:"
        else:
            old_label_text = "Eski Şifre (ilk kez şifre oluşturuyorsan boş bırakabilirsin):"

        self.old_password_label = QLabel(old_label_text)
        self.old_password_edit = QLineEdit()
        self.old_password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.old_password_label)
        layout.addWidget(self.old_password_edit)

        self.new_password_label = QLabel("Yeni Şifre:")
        self.new_password_edit = QLineEdit()
        self.new_password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.new_password_label)
        layout.addWidget(self.new_password_edit)

        self.repeat_password_label = QLabel("Yeni Şifre (Tekrar):")
        self.repeat_password_edit = QLineEdit()
        self.repeat_password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.repeat_password_label)
        layout.addWidget(self.repeat_password_edit)

        btn_layout = QHBoxLayout()
        self.cancel_btn = QPushButton("İptal")
        self.save_btn = QPushButton("Şifreyi Güncelle")
        self.cancel_btn.clicked.connect(self.close)
        self.save_btn.clicked.connect(self.update_password)
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.save_btn)
        layout.addLayout(btn_layout)

    def update_password(self):
        old_pwd = self.old_password_edit.text().strip()
        new_pwd = self.new_password_edit.text().strip()
        repeat_pwd = self.repeat_password_edit.text().strip()

        if not new_pwd or not repeat_pwd:
            QMessageBox.warning(self, "Hata", "Yeni şifre alanları boş bırakılamaz.")
            return

        if new_pwd != repeat_pwd:
            QMessageBox.warning(self, "Hata", "Yeni şifreler birbiriyle eşleşmiyor.")
            return

        if self.mode == "teacher":
            teachers = load_teachers()
            found = None
            for t in teachers:
                if t.get("name", "") == self.name:
                    found = t
                    break
            if found is None:
                QMessageBox.warning(self, "Hata", "Öğretmen kaydı bulunamadı.")
                return
            if found.get("password", "") != old_pwd:
                QMessageBox.warning(self, "Hata", "Eski şifre hatalı.")
                return
            found["password"] = new_pwd
            save_teachers(teachers)
            QMessageBox.information(self, "Başarılı", "Şifre güncellendi.")
            self.close()
        else:
            students = load_students()
            found = None
            for s in students:
                if s.get("name", "") == self.name:
                    found = s
                    break

            if found is None:
                if old_pwd:
                    QMessageBox.warning(self, "Hata", "Bu isimle kayıtlı öğrenci bulunamadı.")
                    return
                students.append({"name": self.name, "password": new_pwd})
                save_students(students)
                QMessageBox.information(self, "Başarılı", "Şifre oluşturuldu.")
                self.close()
            else:
                current_pwd = found.get("password", "")
                if current_pwd:
                    if current_pwd != old_pwd:
                        QMessageBox.warning(self, "Hata", "Eski şifre hatalı.")
                        return
                found["password"] = new_pwd
                save_students(students)
                QMessageBox.information(self, "Başarılı", "Şifre güncellendi.")
                self.close()


class LoginWindow(QWidget):
    def __init__(self, mode: str, results: Dict[str, Any], teachers: list):
        super().__init__()
        self.mode = mode
        self.results = results
        self.teachers = teachers
        self.selected_teacher_name = None
        self.setFixedSize(500, 460)
        if mode == "student":
            self.setWindowTitle("Öğrenci Girişi")
        else:
            self.setWindowTitle("Öğretmen Girişi")
        self.setStyleSheet(
            "QWidget {background-color: #020617; color: white;}"
            "QPushButton {background-color: #2563eb; color: white; border-radius: 10px; padding: 10px; font-size: 15px;}"
            "QPushButton:hover {background-color: #3b82f6;}"
            "QLineEdit {background-color: #020617; color: white; padding: 8px; border-radius: 8px; border: 1px solid #1d4ed8;}"
            "QLabel {font-size: 14px;}"
            "QComboBox {background-color: #020617; color: white; padding: 6px; border-radius: 8px; border: 1px solid #1d4ed8;}"
        )
        layout = QVBoxLayout(self)
        layout.setSpacing(18)
        title = QLabel("Öğrenci Modu" if mode == "student" else "Öğretmen Modu")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title)
        self.name_label = QLabel("İsim Soyisim:")
        self.name_edit = QLineEdit()
        layout.addWidget(self.name_label)
        layout.addWidget(self.name_edit)
        if self.mode == "student":
            self.teacher_label = QLabel("Öğretmen Seç:")
            self.teacher_combo = QComboBox()
            for t in self.teachers:
                self.teacher_combo.addItem(t.get("name", ""))
            layout.addWidget(self.teacher_label)
            layout.addWidget(self.teacher_combo)
            if not self.teachers:
                self.teacher_combo.setEnabled(False)
                self.teacher_label.setText("Öğretmen bulunamadı, önce öğretmen kaydı oluşturun.")
        self.password_label = QLabel("Şifre:")
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.password_label)
        layout.addWidget(self.password_edit)
        if self.mode == "student":
            self.password_label.setText("Şifre (isteğe bağlı, tanımlı şifren varsa zorunlu):")
        btn_layout = QHBoxLayout()
        self.back_btn = QPushButton("Geri")
        self.start_btn = QPushButton("Devam")
        self.change_password_btn = QPushButton("Şifre Değiştir")
        self.back_btn.clicked.connect(self.go_back)
        self.start_btn.clicked.connect(self.start_mode)
        self.change_password_btn.clicked.connect(self.open_password_change)
        btn_layout.addWidget(self.back_btn)
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.change_password_btn)
        layout.addLayout(btn_layout)

    def go_back(self):
        teachers = load_teachers()
        self.mode_window = ModeWindow(self.results, teachers)
        self.mode_window.show()
        self.close()

    def open_password_change(self):
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Uyarı", "Önce isim soyisim alanını doldurun.")
            return
        self.pw_window = PasswordChangeWindow(self.mode, name)
        self.pw_window.show()

    def start_mode(self):
        name = self.name_edit.text().strip()
        pwd = self.password_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Uyarı", "İsim Soyisim alanı boş bırakılamaz.")
            return
        if self.mode == "teacher":
            teachers = load_teachers()
            matched = None
            for t in teachers:
                if t.get("name", "") == name and t.get("password", "") == pwd:
                    matched = t
                    break
            if matched is None:
                QMessageBox.warning(self, "Hata", "Öğretmen adı veya şifre hatalı.")
                return
            self.teacher_window = TeacherMainWindow(self.results, name)
            self.teacher_window.show()
            self.close()
        else:
            if not self.teachers:
                QMessageBox.warning(self, "Hata", "Kayıtlı öğretmen bulunamadı. Önce öğretmen kaydı oluşturun.")
                return
            teacher_name = self.teacher_combo.currentText().strip()
            if not teacher_name:
                QMessageBox.warning(self, "Hata", "Lütfen bir öğretmen seçin.")
                return
            students = load_students()
            student_record = None
            for s in students:
                if s.get("name", "") == name:
                    student_record = s
                    break
            if student_record and student_record.get("password", ""):
                if not pwd:
                    QMessageBox.warning(self, "Hata", "Bu öğrenci için şifre tanımlanmış. Lütfen şifrenizi girin.")
                    return
                if pwd != student_record.get("password", ""):
                    QMessageBox.warning(self, "Hata", "Şifre hatalı.")
                    return
            self.exam_setup = ExamSetupWindow(self.results, name, teacher_name)
            self.exam_setup.show()
            self.close()

class ExamSetupWindow(QWidget):
    def __init__(self, results: Dict[str, Any], student_name: str, teacher_name: str):
        super().__init__()
        self.results = results
        self.student_name = student_name
        self.teacher_name = teacher_name
        self.setWindowTitle("Sınav Ayarları")
        self.setFixedSize(420, 260)
        self.setStyleSheet(
            "QWidget {background-color: #020617; color: white;}"
            "QPushButton {background-color: #2563eb; color: white; border-radius: 10px; padding: 8px; font-size: 14px;}"
            "QPushButton:hover {background-color: #3b82f6;}"
            "QLineEdit {background-color: #020617; color: white; padding: 8px; border-radius: 8px; border: 1px solid #1d4ed8;}"
            "QLabel {font-size: 14px;}"
        )
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        title = QLabel("Sınav Süresi Seçimi")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)
        info = QLabel("Dakika cinsinden süre girin (boş bırakılırsa sınırsız):")
        layout.addWidget(info)
        self.duration_edit = QLineEdit()
        self.duration_edit.setPlaceholderText("Örn: 15")
        layout.addWidget(self.duration_edit)
        btn_layout = QHBoxLayout()
        self.back_btn = QPushButton("Geri")
        self.start_btn = QPushButton("Sınavı Başlat")
        self.change_password_btn = QPushButton("Şifre Değiştir")
        self.back_btn.clicked.connect(self.go_back)
        self.start_btn.clicked.connect(self.start_exam)
        self.change_password_btn.clicked.connect(self.change_password)
        btn_layout.addWidget(self.back_btn)
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.change_password_btn)
        layout.addLayout(btn_layout)

    def go_back(self):
        teachers = load_teachers()
        self.login = LoginWindow("student", self.results, teachers)
        self.login.show()
        self.close()

    def start_exam(self):
        text = self.duration_edit.text().strip()
        exam_end_time = None
        if text:
            if not text.isdigit() or int(text) <= 0:
                QMessageBox.warning(self, "Hata", "Geçerli bir dakika değeri girin.")
                return
            minutes = int(text)
            exam_end_time = datetime.now() + timedelta(minutes=minutes)
        easy, medium, hard = build_question_bank()
        questions = build_exam_questions(easy, medium, hard, per_level=5)
        quiz = Quiz(questions, exam_end_time=exam_end_time)
        self.quiz_window = QuizWindow(self.results, self.student_name, self.teacher_name, quiz)
        self.quiz_window.show()
        self.close()

    def change_password(self):
        self.pw_window = PasswordChangeWindow("student", self.student_name)
        self.pw_window.show()

class QuizWindow(QWidget):
    def __init__(self, results: Dict[str, Any], student_name: str, teacher_name: str, quiz: Quiz):
        super().__init__()
        self.results = results
        self.student_name = student_name
        self.teacher_name = teacher_name
        self.quiz = quiz
        self.setWindowTitle("Sınav")
        self.setFixedSize(720, 480)
        self.setStyleSheet(
            "QWidget {background-color: #020617; color: white;}"
            "QPushButton {background-color: #2563eb; color: white; border-radius: 10px; padding: 8px; font-size: 14px;}"
            "QPushButton:hover {background-color: #3b82f6;}"
            "QLabel {font-size: 14px;}"
        )
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        header_layout = QHBoxLayout()
        self.lbl_info = QLabel("")
        self.lbl_info.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.lbl_time = QLabel("")
        self.lbl_time.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_time.setStyleSheet(
            "font-size: 14px; padding: 6px 14px; border-radius: 10px; "
            "background-color: #020617; border: 1px solid #1d4ed8;"
        )
        header_layout.addWidget(self.lbl_info)
        header_layout.addWidget(self.lbl_time, alignment=Qt.AlignmentFlag.AlignRight)
        layout.addLayout(header_layout)
        self.lbl_question = QLabel("")
        self.lbl_question.setWordWrap(True)
        self.lbl_question.setStyleSheet("font-size: 16px; margin-top: 10px;")
        layout.addWidget(self.lbl_question)
        self.choice_buttons = []
        for i in range(4):
            btn = QPushButton("")
            btn.clicked.connect(self.make_answer_handler(i))
            self.choice_buttons.append(btn)
            layout.addWidget(btn)
        self.lbl_feedback = QLabel("")
        self.lbl_feedback.setStyleSheet("font-size: 14px; margin-top: 8px;")
        layout.addWidget(self.lbl_feedback)
        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()
        self.finish_btn = QPushButton("Sınavı Bitir")
        self.finish_btn.clicked.connect(self.finish_early)
        bottom_layout.addWidget(self.finish_btn)
        layout.addLayout(bottom_layout)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        if self.quiz.exam_end_time is not None:
            self.timer.start(1000)
        self.load_question()

    def make_answer_handler(self, index):
        def handler():
            self.handle_answer(index)
        return handler

    def update_time(self):
        total = self.quiz.get_remaining_time()
        if total <= 0:
            self.lbl_time.setText("Kalan süre: 00:00")
            self.timer.stop()
            self.quiz.early_terminated = True
            self.quiz.index = len(self.quiz.questions)
            self.finish_exam()
            return
        minutes = total // 60
        seconds = total % 60
        self.lbl_time.setText(f"Kalan süre: {minutes:02d}:{seconds:02d}")

    def load_question(self):
        if not self.quiz.has_more_questions():
            self.finish_exam()
            return
        soru = self.quiz.get_current_question()
        current_index = self.quiz.index + 1
        total = len(self.quiz.questions)
        self.lbl_info.setText(f"Soru {current_index}/{total} - Seviye: {soru.level}")
        self.lbl_question.setText(soru.text)
        for i, btn in enumerate(self.choice_buttons):
            if i < len(soru.choices):
                btn.setText(soru.choices[i])
                btn.setEnabled(True)
                btn.show()
            else:
                btn.hide()
        if self.quiz.exam_end_time is None:
            self.lbl_time.setText("Süre: sınırsız")
        self.lbl_feedback.setText("")

    def handle_answer(self, index):
        if not self.quiz.has_more_questions():
            return
        soru = self.quiz.get_current_question()
        if index >= len(soru.choices):
            return
        correct = self.quiz.answer_current(index)
        if correct:
            self.lbl_feedback.setText("✅ Doğru cevap!")
        else:
            self.lbl_feedback.setText(f"❌ Yanlış! Doğru cevap: {soru.answer}")
        self.load_question()

    def finish_early(self):
        self.quiz.early_terminated = True
        self.quiz.index = len(self.quiz.questions)
        self.finish_exam()

    def finish_exam(self):
        if self.timer.isActive():
            self.timer.stop()
        (
            correct,
            wrong,
            percent,
            answered,
            total_questions,
            points,
            max_points,
            point_percent,
            level_label,
            level_stats,
        ) = self.quiz.get_results()
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        weak_info = analyze_weak_areas(level_stats)
        study_suggestions = build_study_suggestions(level_label, level_stats)
        new_record = {
            "datetime": now_str,
            "correct": correct,
            "wrong": wrong,
            "percent": percent,
            "answered": answered,
            "total_questions": total_questions,
            "early_terminated": self.quiz.early_terminated,
            "points": points,
            "max_points": max_points,
            "point_percent": point_percent,
            "level_label": level_label,
            "level_stats": level_stats,
            "study_suggestions": study_suggestions,
            "teacher": self.teacher_name,
        }
        user_records = self.results.get(self.student_name, [])
        user_records.append(new_record)
        self.results[self.student_name] = user_records
        save_results(self.results)
        self.result_window = ResultWindow(
            self.student_name,
            now_str,
            correct,
            wrong,
            percent,
            answered,
            total_questions,
            points,
            max_points,
            point_percent,
            level_label,
            level_stats,
            weak_info,
            study_suggestions,
        )
        self.result_window.show()
        self.close()

class ResultWindow(QWidget):
    def __init__(
        self,
        student_name: str,
        datetime_str: str,
        correct: int,
        wrong: int,
        percent: float,
        answered: int,
        total_questions: int,
        points: int,
        max_points: int,
        point_percent: float,
        level_label: str,
        level_stats: dict,
        weak_info: str,
        study_suggestions: list,
    ):
        super().__init__()
        self.setWindowTitle("Sınav Sonuçları")
        self.setFixedSize(720, 520)
        self.setStyleSheet(
            "QWidget {background-color: #020617; color: white;}"
            "QPushButton {background-color: #2563eb; color: white; border-radius: 10px; padding: 8px; font-size: 14px;}"
            "QPushButton:hover {background-color: #3b82f6;}"
            "QLabel {font-size: 14px;}"
            "QPlainTextEdit {background-color: #020617; color: white; border-radius: 8px; padding: 6px; border: 1px solid #1f2937;}"
        )
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        title = QLabel("SON SINAV ÖZETİ")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title)
        info = QLabel(
            f"Ad Soyad: {student_name} | Tarih: {datetime_str} | Seviye: {level_label}"
        )
        layout.addWidget(info)
        stat_label = QLabel(
            f"Sorular: {answered}/{total_questions} | Doğru: {correct} | Yanlış: {wrong} | "
            f"Soru Başarısı: {percent:.2f}% | Puan: {points}/{max_points} ({point_percent:.2f}%)"
        )
        layout.addWidget(stat_label)
        level_label_widget = QLabel("Seviye bazlı istatistikler:")
        layout.addWidget(level_label_widget)
        level_text_lines = []
        for level in ["Kolay", "Orta", "Zor"]:
            stats = level_stats[level]
            total_lv = stats["correct"] + stats["wrong"]
            if total_lv == 0:
                continue
            acc_lv = (stats["correct"] / total_lv) * 100
            level_text_lines.append(
                f"{level:<5} -> Doğru: {stats['correct']}, Yanlış: {stats['wrong']} (Başarı: {acc_lv:.2f}%)"
            )
        level_box = QPlainTextEdit()
        level_box.setReadOnly(True)
        level_box.setPlainText("\n".join(level_text_lines) if level_text_lines else "Veri yok.")
        layout.addWidget(level_box)
        weak_label = QLabel("Zorlandığın seviye analizi:")
        layout.addWidget(weak_label)
        weak_box = QPlainTextEdit()
        weak_box.setReadOnly(True)
        weak_box.setPlainText(weak_info)
        layout.addWidget(weak_box)
        sug_label = QLabel("Önerilen çalışma konuları:")
        layout.addWidget(sug_label)
        sug_box = QPlainTextEdit()
        sug_box.setReadOnly(True)
        sug_box.setPlainText("\n".join(f"- {s}" for s in study_suggestions))
        layout.addWidget(sug_box)
        btn = QPushButton("Kapat")
        btn.clicked.connect(self.close_app)
        layout.addWidget(btn)

    def close_app(self):
        QApplication.instance().quit()

class TeacherMainWindow(QWidget):
    def __init__(self, results: Dict[str, Any], teacher_name: str):
        super().__init__()
        self.results = results
        self.teacher_name = teacher_name
        self.setWindowTitle("Öğretmen Paneli")
        self.setFixedSize(800, 550)
        self.setStyleSheet(
            "QWidget {background-color: #020617; color: white;}"
            "QPushButton {background-color: #2563eb; color: white; border-radius: 10px; padding: 8px; font-size: 14px;}"
            "QPushButton:hover {background-color: #3b82f6;}"
            "QLabel {font-size: 14px;}"
            "QPlainTextEdit {background-color: #020617; color: white; border-radius: 8px; padding: 6px; border: 1px solid #1f2937;}"
            "QListWidget {background-color: #020617; color: white; border-radius: 8px; border: 1px solid #1f2937;}"
            "QLineEdit {background-color: #020617; color: white; padding: 6px; border-radius: 8px; border: 1px solid #1f2937;}"
            "QComboBox {background-color: #020617; color: white; padding: 6px; border-radius: 8px; border: 1px solid #1f2937;}"
        )
        layout = QVBoxLayout(self)
        title = QLabel("Öğretmen Paneli")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 22px; font-weight: bold;")
        layout.addWidget(title)
        header_buttons_layout = QHBoxLayout()
        header_buttons_layout.addStretch()
        self.change_password_btn = QPushButton("Şifremi Değiştir")
        self.change_password_btn.clicked.connect(self.open_password_change)
        header_buttons_layout.addWidget(self.change_password_btn)
        layout.addLayout(header_buttons_layout)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        self.tab_general = QWidget()
        self.tab_student = QWidget()
        self.tab_questions = QWidget()
        self.tabs.addTab(self.tab_general, "Genel Rapor")
        self.tabs.addTab(self.tab_student, "Öğrenci Detayları")
        self.tabs.addTab(self.tab_questions, "Soru Bankası")
        self.setup_general_tab()
        self.setup_student_tab()
        self.setup_questions_tab()
        self.refresh_general_report()
        self.refresh_student_list()
        self.refresh_question_counts()

    def open_password_change(self):
        self.pw_window = PasswordChangeWindow("teacher", self.teacher_name)
        self.pw_window.show()

    def setup_general_tab(self):
        layout = QVBoxLayout(self.tab_general)
        label = QLabel("Genel sınav istatistikleri:")
        layout.addWidget(label)
        self.general_text = QPlainTextEdit()
        self.general_text.setReadOnly(True)
        layout.addWidget(self.general_text)
        refresh_btn = QPushButton("Yenile")
        refresh_btn.clicked.connect(self.refresh_general_report)
        layout.addWidget(refresh_btn, alignment=Qt.AlignmentFlag.AlignRight)

    def setup_student_tab(self):
        layout = QHBoxLayout(self.tab_student)
        left_layout = QVBoxLayout()
        right_layout = QVBoxLayout()
        label = QLabel("Öğrenciler:")
        left_layout.addWidget(label)
        self.student_list = QListWidget()
        self.student_list.currentTextChanged.connect(self.show_student_detail)
        left_layout.addWidget(self.student_list)
        layout.addLayout(left_layout, 1)
        detail_label = QLabel("Seçili öğrencinin sınav detayları:")
        right_layout.addWidget(detail_label)
        self.student_detail_text = QPlainTextEdit()
        self.student_detail_text.setReadOnly(True)
        right_layout.addWidget(self.student_detail_text)
        layout.addLayout(right_layout, 2)

    def setup_questions_tab(self):
        layout = QVBoxLayout(self.tab_questions)
        self.lbl_counts = QLabel("")
        layout.addWidget(self.lbl_counts)
        form_layout = QVBoxLayout()
        self.level_combo = QComboBox()
        self.level_combo.addItems(["Kolay", "Orta", "Zor"])
        form_layout.addWidget(QLabel("Soru seviyesi:"))
        form_layout.addWidget(self.level_combo)
        self.question_edit = QPlainTextEdit()
        self.question_edit.setPlaceholderText("Soru metni")
        form_layout.addWidget(self.question_edit)
        self.choice_edits = []
        for i in range(4):
            le = QLineEdit()
            le.setPlaceholderText(f"{i+1}. şık")
            self.choice_edits.append(le)
            form_layout.addWidget(le)
        self.correct_combo = QComboBox()
        self.correct_combo.addItems(["1", "2", "3", "4"])
        form_layout.addWidget(QLabel("Doğru şık numarası:"))
        form_layout.addWidget(self.correct_combo)
        self.add_question_btn = QPushButton("Soruyu Ekle")
        self.add_question_btn.clicked.connect(self.add_question)
        form_layout.addWidget(self.add_question_btn, alignment=Qt.AlignmentFlag.AlignRight)
        layout.addLayout(form_layout)

    def refresh_general_report(self):
        text = build_teacher_general_report(self.results)
        self.general_text.setPlainText(text)

    def refresh_student_list(self):
        self.student_list.clear()
        names = sorted(self.results.keys())
        self.student_list.addItems(names)

    def show_student_detail(self, name: str):
        if not name:
            self.student_detail_text.setPlainText("")
            return
        text = build_teacher_student_detail_text(self.results, name)
        self.student_detail_text.setPlainText(text)

    def refresh_question_counts(self):
        data = load_custom_questions()
        self.lbl_counts.setText(
            f"Mevcut ekstra soru sayıları -> Kolay: {len(data['easy'])} | Orta: {len(data['medium'])} | Zor: {len(data['hard'])}"
        )

    def add_question(self):
        level_label = self.level_combo.currentText()
        if level_label == "Kolay":
            level_key = "easy"
        elif level_label == "Orta":
            level_key = "medium"
        else:
            level_key = "hard"
        text = self.question_edit.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "Hata", "Soru metni boş olamaz.")
            return
        choices = []
        for le in self.choice_edits:
            c = le.text().strip()
            if not c:
                QMessageBox.warning(self, "Hata", "Tüm şıklar doldurulmalıdır.")
                return
            choices.append(c)
        correct_index = int(self.correct_combo.currentText()) - 1
        answer = choices[correct_index]
        data = load_custom_questions()
        qd = {
            "text": text,
            "choices": choices,
            "answer": answer,
        }
        data[level_key].append(qd)
        save_custom_questions(data)
        self.question_edit.clear()
        for le in self.choice_edits:
            le.clear()
        self.correct_combo.setCurrentIndex(0)
        self.refresh_question_counts()
        QMessageBox.information(self, "Başarılı", f"Soru eklendi. Seviye: {level_label}")

def main():
    results = load_results()
    teachers = load_teachers()
    app = QApplication(sys.argv)
    window = ModeWindow(results, teachers)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
