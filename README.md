<div align="center">

<img src="icon-512.png" alt="ALTRA-DAWNLOADER" width="120" height="120">

# ALTRA-DAWNLOADER

**محمّل وسائط مستقل وقابل للتثبيت · Independent, installable media downloader**

[![Live App](https://img.shields.io/badge/Live%20App-افتح%20التطبيق-00d2ff?style=for-the-badge&logo=googlechrome&logoColor=white)](https://danial56hd-wq.github.io/ALTRA-DAWNLOADER/)
[![Version](https://img.shields.io/badge/version-7.1-00ff88?style=for-the-badge)](#)
[![PWA](https://img.shields.io/badge/PWA-installable-5a0fc8?style=for-the-badge&logo=pwa&logoColor=white)](#-التثبيت)
[![License: MIT](https://img.shields.io/badge/License-MIT-ff9f43?style=for-the-badge)](LICENSE)

[**🚀 افتح التطبيق**](https://danial56hd-wq.github.io/ALTRA-DAWNLOADER/) ·
[**📦 المستودع**](https://github.com/danial56hd-wq/ALTRA-DAWNLOADER) ·
[**✉️ تواصل**](#-التواصل-والحسابات)

</div>

---

## 🌐 الروابط

| | الرابط |
|---|---|
| **التطبيق المباشر** | https://danial56hd-wq.github.io/ALTRA-DAWNLOADER/ |
| **المستودع** | https://github.com/danial56hd-wq/ALTRA-DAWNLOADER |

---

## ✨ نبذة

**ALTRA-DAWNLOADER** تطبيق ويب تقدّمي (PWA) لتحميل الفيديو والصوت بصيغ متعددة، بحد أقصى **10 مهام متزامنة**.
يعمل مباشرة من المتصفح، ويُثبَّت على الهاتف أو سطح المكتب كتطبيق مستقل، ولا يحتاج إلى حساب أو تسجيل.

- ملفات واجهة ثابتة فقط: `HTML + CSS + JavaScript`، بلا أي اعتماد على أطر عمل أو خادم خلفي.
- كل الإعدادات والسجل تُحفظ محليًا على جهازك.
- واجهة عربية بالكامل بتصميم داكن يدعم الاتجاه من اليمين إلى اليسار.

## 🎯 المزايا

| الميزة | الوصف |
|---|---|
| ⚡ **تحميل فوري** | الصق الرابط واضغط GO، أو شاركه إلى التطبيق مباشرة |
| 🔗 **المشاركة إلى التطبيق** | من أي تطبيق على أندرويد: مشاركة ← ALTRA (Web Share Target) |
| 🔢 **حتى 10 مهام** | قائمة انتظار بتزامن قابل للضبط من 1 إلى 10 |
| 📁 **مجلد حفظ مخصص** | اختيار مجلد داخلي أو خارجي على المتصفحات الداعمة (File System Access API) |
| 🎚️ **جودة وصيغ** | من 360p إلى 4K، وصيغ MP4 وWEBM وMP3 وOGG وOPUS وWAV |
| 🔍 **بحث متقدم** | فلترة المهام والسجل حسب الكلمة والحالة والمنصة |
| 📊 **سجل وإحصائيات** | سجل التحميلات، مع تصدير بصيغة JSON |
| 📲 **قابل للتثبيت** | أيقونة على الشاشة الرئيسية، ويعمل بوضع ملء الشاشة |
| 🛠️ **Console مدمج** | شاشة تتبع للأخطاء وأوامر `help` و`status` و`queue` و`storage` |
| 📤 **مشاركة التطبيق** | واتساب، تيليغرام، بريد، أو نسخ الرابط |

## 📲 التثبيت

### أندرويد (Chrome)
1. افتح الرابط: https://danial56hd-wq.github.io/ALTRA-DAWNLOADER/
2. اضغط **⋮** ثم **تثبيت التطبيق** (أو **إضافة إلى الشاشة الرئيسية**).
3. بعد التثبيت ستظهر **ALTRA** في قائمة المشاركة داخل التطبيقات الأخرى.

### iPhone / iPad (Safari)
1. افتح الرابط في Safari.
2. اضغط **مشاركة** ثم **إضافة إلى الشاشة الرئيسية**.

### الكمبيوتر (Chrome / Edge)
1. افتح الرابط.
2. اضغط أيقونة التثبيت في شريط العنوان، أو **تثبيت** داخل التطبيق.

## 🚀 الاستخدام السريع

1. افتح التطبيق.
2. الصق رابطًا أو أكثر في الحقل، رابط في كل سطر.
3. اضغط **GO · ابدأ التحميل**.
4. تابع التقدم في **قائمة الانتظار**، واضغط **إلغاء** أو **إعادة** عند الحاجة.

> **اختصار:** `Ctrl + Enter` لبدء التحميل من الحقل على الكمبيوتر.

## ⚙️ ما يعمل وما يحتاج خادمًا

| نوع الرابط | يعمل بدون خادم؟ | ملاحظات |
|---|:---:|---|
| ملف مباشر (`.mp4` `.mp3` `.webm` `.m4a` …) | ✅ | يعمل فورًا، وإن منع الموقع الاتصال (CORS) يمرّره التطبيق لتنزيل المتصفح |
| YouTube · Instagram · TikTok · X · Reddit · Facebook | ❌ | يحتاج خادم **Cobalt** أو واجهة **yt-dlp** خاصة بك |

**سبب ذلك:** المتصفحات تمنع استخراج روابط الوسائط من هذه المواقع مباشرة (CORS وحمايات الموقع).
ولا يمكن لتطبيق ثابت تجاوز ذلك بنفسه، كما أن خوادم Cobalt العامة كثيرًا ما تطلب تحققًا أو تتوقف عن العمل.

### ربط خادمك الخاص
1. شغّل خادم [Cobalt](https://github.com/imputnet/cobalt) على استضافتك.
2. افتح القائمة **☰ ← الإعدادات**.
3. ضع عنوانه في **رابط خادمك الخاص**، مثل `https://my-server.example`.
4. اختر محرك الاستخراج **خادمي الخاص + مباشر**.

## 🧱 بنية المشروع

```text
ALTRA-DAWNLOADER/
├── index.html            # الواجهة والمنطق كاملًا
├── sw.js                 # Service Worker للعمل دون اتصال
├── manifest.webmanifest  # بيانات التثبيت والمشاركة إلى التطبيق
├── icon-192.png          # أيقونة التثبيت
├── icon-512.png          # أيقونة التثبيت الكبيرة
├── README.md
└── LICENSE
```

## 🛠️ التشغيل والتطوير محليًا

لا حاجة لبناء أو تثبيت حزم. يكفي خادم ملفات ثابتة:

```bash
git clone https://github.com/danial56hd-wq/ALTRA-DAWNLOADER.git
cd ALTRA-DAWNLOADER
python3 -m http.server 8080
```

ثم افتح `http://localhost:8080`. عنوان `localhost` يُعامَل كبيئة آمنة، فيعمل معه التثبيت والـ Service Worker.

## 🚢 النشر على GitHub Pages

1. افتح **Settings ← Pages**.
2. **Source:** Deploy from a branch.
3. **Branch:** `main` والمجلد `/ (root)` ثم **Save**.

## 🔧 استكشاف الأخطاء

| المشكلة | الحل |
|---|---|
| لا يظهر خيار التثبيت | تأكد أنك على رابط HTTPS، وجرّب تحديث الصفحة، ثم افتح قائمة المتصفح |
| تظهر «تعذّر الاتصال بالمصدر» | الموقع يمنع CORS أو أنك دون إنترنت؛ جرّب رابط ملف مباشر أو ضع خادمك الخاص |
| الروابط الاجتماعية تفشل | خوادم Cobalt العامة تتطلب تحققًا؛ استخدم خادمًا خاصًا |
| التطبيق لا يحمّل التحديثات | أغلقه وأعد فتحه، أو امسح بيانات الموقع من إعدادات المتصفح |
| مجلد الحفظ لا يعمل | الميزة مدعومة في Chrome وEdge على سطح المكتب؛ على الجوال يُستخدم حفظ الملف العادي |

افتح **☰ ← Console** لرؤية سجل الأخطاء، وأرفقه عند التبليغ عن مشكلة.

## ⚖️ إخلاء المسؤولية

- هذا التطبيق أداة تقنية فقط، ولا يتجاوز حماية **DRM** ولا يخترق أي حماية.
- حمّل **المحتوى الذي يحق لك تحميله فقط**، والتزم بشروط كل منصة وبقوانين حقوق النشر في بلدك.
- المطوّر غير مسؤول عن أي استخدام مخالف.

## 🤝 المساهمة

المساهمات مرحّب بها:
1. اعمل **Fork** للمستودع.
2. أنشئ فرعًا للتعديل: `git checkout -b feature/اسم-الميزة`
3. أرسل **Pull Request** مع وصف واضح للتغيير.

كما يمكنك فتح **Issue** للاقتراحات أو الأخطاء.

## 📞 التواصل والحسابات

**نضال وطفة · Nidal Watfa**

| المنصة | الرابط |
|---|---|
| 📧 البريد | [nidalwatfa99@gmail.com](mailto:nidalwatfa99@gmail.com) |
| 💬 واتساب | [0096998854450](https://wa.me/96998854450) |
| ✈️ تيليغرام | [@nidal12watfa](https://t.me/nidal12watfa) |
| 🐙 GitHub | [danial56hd-wq](https://github.com/danial56hd-wq) |
| 🦊 GitLab | [danial-wq](https://gitlab.com/danial-wq) |
| 🌿 Codeberg | [nidalwatfa](https://codeberg.org/nidalwatfa) |
| 💼 LinkedIn | [nidal-watfa](https://www.linkedin.com/in/nidal-watfa-a91720301) |
| 𝕏 X | [@NidalWatfa12501](https://x.com/NidalWatfa12501) |
| 🎓 ORCID | [0009-0003-2462-6630](https://orcid.org/0009-0003-2462-6630) |

## 📄 الترخيص

مرخّص بموجب [رخصة MIT](LICENSE). © 2026 Nidal Watfa.

---

<div align="center">

### English summary

**ALTRA-DAWNLOADER** is a dependency-free, installable PWA media downloader: up to 10 concurrent tasks,
direct-file downloads with no server, Web Share Target support, custom save folder, history and advanced search.
Social platforms (YouTube, Instagram, TikTok…) require your own [Cobalt](https://github.com/imputnet/cobalt) server because browsers block extracting those links.

**[Open the app](https://danial56hd-wq.github.io/ALTRA-DAWNLOADER/)** · Licensed under MIT.

</div>

