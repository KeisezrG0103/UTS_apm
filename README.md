# Proses Pengumpulan, Pembersihan, dan Persiapan Data

## 1. Gambaran Umum

Tugas ini menggunakan data percakapan publik dari media sosial **Facebook** dan **X (Twitter)** yang berkaitan dengan topik program **cek kesehatan gratis** serta kebijakan atau diskusi yang relevan dengan topik tersebut.  
Dataset dibangun melalui proses *scraping* menggunakan Python dan Selenium, kemudian dilanjutkan dengan tahap pembersihan, penggabungan, penyaringan, dan penyusunan ulang data agar siap digunakan untuk analisis maupun pemodelan.

---

## 2. Metode Pengumpulan Data

### 2.1 Pendekatan yang Digunakan

Proses pengumpulan data dilakukan dengan pendekatan **web scraping semi-manual**.  
Metode ini dipilih karena konten media sosial bersifat dinamis, sering berubah, dan tidak selalu mudah diakses melalui scraping statis biasa.

Secara umum alurnya adalah sebagai berikut:

1. Browser dibuka secara otomatis menggunakan Selenium.
2. Pengguna melakukan login atau navigasi manual ke halaman target.
3. Pengguna memilih topik, kata kunci, grup, halaman, atau hasil pencarian yang relevan.
4. Script melakukan pengambilan teks postingan atau tweet secara berulang melalui proses scroll.
5. Data hasil scraping disimpan ke dalam file CSV.

### 2.2 Pengumpulan Data dari X

Pada platform X, scraping dilakukan menggunakan Selenium dengan browser Chrome.  
Pengguna membuka X, melakukan pencarian manual berdasarkan kata kunci yang relevan, lalu script mengambil tweet dari elemen yang sesuai pada halaman.

Ciri utama proses ini:

- login dilakukan secara manual oleh pengguna,
- pencarian dilakukan berdasarkan kata kunci atau tagar,
- data dikumpulkan dari hasil scroll berulang,
- tweet yang sudah terbaca disimpan ke dalam struktur data unik untuk menghindari duplikasi.

### 2.3 Pengumpulan Data dari Facebook

Pada platform Facebook, scraping dilakukan menggunakan Selenium dengan browser Microsoft Edge.  
Pengguna diarahkan untuk mencari halaman, grup, atau postingan yang relevan, lalu script mengekstrak teks postingan dari elemen HTML yang sesuai.

Ciri utama proses ini:

- browser dibuka otomatis,
- pengguna memilih target secara manual,
- script mengekstrak isi postingan setelah elemen diperluas,
- proses scroll digunakan untuk memuat lebih banyak konten,
- hasil akhir disimpan dalam bentuk CSV.

---

## 3. Tools dan Teknologi yang Digunakan

Beberapa tools dan teknologi yang digunakan dalam proyek ini adalah:

- **Python**: bahasa pemrograman utama
- **Selenium WebDriver**: untuk otomatisasi browser dan scraping
- **Pandas**: untuk pengolahan data tabular dan penyimpanan CSV
- **Jupyter Notebook**: untuk eksplorasi dan preprocessing data
- **Streamlit**: untuk membangun dashboard analisis interaktif
- **Google Chrome** dan **Microsoft Edge**: browser untuk proses scraping
- **JSON / JSONL**: format penyimpanan data untuk tahap lanjut
- **Plotly** dan **Matplotlib / Seaborn**: untuk visualisasi data

---

## 4. Cakupan Sumber Data dan Periode Waktu

### 4.1 Sumber Data

Sumber data pada proyek ini berasal dari dua platform media sosial:

- **Facebook**
- **X (Twitter)**

Topik data berfokus pada isu yang berkaitan dengan:

- `cek kesehatan gratis`
- `ckg`
- `kesehatan gratis`
- variasi keyword terkait Prabowo dan kebijakan kesehatan
- topik yang muncul dalam diskusi publik yang masih relevan dengan program tersebut

### 4.2 Periode Pengambilan Data

Berdasarkan file hasil scraping yang tersedia di workspace, data dikumpulkan dalam beberapa periode, terutama pada:

- **Maret 2026**
- **April 2026**

File-file hasil scraping menunjukkan timestamp pada beberapa tanggal berikut:

- `2026-03-18`
- `2026-03-19`
- `2026-04-08`
- `2026-04-09`

Dengan demikian, dataset merepresentasikan potret percakapan publik pada rentang waktu tersebut.

---

## 5. Struktur Data Hasil Scraping

Hasil scraping disimpan ke dalam beberapa file CSV, misalnya:

- `FB_scrap_*.csv`
- `X_feedback_kumpulan_*.csv`

Pada tahap berikutnya, file-file CSV digabung dan dibersihkan sehingga menjadi data yang lebih konsisten.  
Kolom teks utama yang dipakai untuk analisis biasanya adalah:

- `Isi Tweet`
- `Isi Postingan`

Setelah preprocessing, kolom-kolom tersebut digabung menjadi satu kolom utama bernama:

- `narasi`

---

## 6. Proses Pembersihan Data

Pembersihan data dilakukan secara bertahap untuk memastikan dataset siap dianalisis dan digunakan pada pemodelan.

### 6.1 Penggabungan Data

Pada tahap awal, seluruh file CSV pada folder raw dibaca dan digabung menjadi satu DataFrame.  
Jika terdapat beberapa kolom teks, seperti `Isi Tweet` dan `Isi Postingan`, maka kolom-kolom tersebut digabung menjadi satu kolom teks utama, yaitu `narasi`.

Tujuan langkah ini adalah:

- menyatukan semua narasi teks dalam format yang seragam,
- memudahkan proses filtering dan analisis teks,
- menghindari perbedaan struktur antar sumber data.

### 6.2 Penghapusan Data Duplikat

Setelah penggabungan, data duplikat dicek dan dihapus menggunakan fungsi `drop_duplicates()`.  
Langkah ini penting untuk menghindari bias akibat postingan yang muncul berulang kali.

### 6.3 Penghapusan Baris Tidak Relevan

Baris yang hanya berisi tagar, spasi kosong, atau teks yang tidak memiliki makna naratif dibuang.  
Contohnya adalah baris yang setelah tagar dihapus menjadi kosong.

### 6.4 Filtering Berdasarkan Topik

Data kemudian difilter agar hanya menyisakan postingan yang relevan dengan topik penelitian.  
Filtering ini dilakukan menggunakan kata kunci seperti:

- `prabowo`
- `ckg`
- `kesehatan gratis`
- `cek kesehatan gratis`
- variasi kata kunci lain yang serupa

Langkah ini bertujuan untuk memastikan bahwa dataset final benar-benar fokus pada topik penelitian.

### 6.5 Pembersihan Teks

Teks juga dibersihkan dari berbagai karakter yang tidak diperlukan, misalnya:

- newline `\n`
- carriage return `\r`
- tab `\t`
- spasi berlebih
- karakter khusus yang tidak relevan
- tanda baca ganda
- format bold atau simbol yang muncul pada file JSONL

Pembersihan ini dilakukan agar teks menjadi lebih rapi, konsisten, dan siap diproses lebih lanjut.

### 6.6 Normalisasi Teks

Pada beberapa tahap, teks juga diubah menjadi huruf kecil agar pencocokan keyword dan analisis teks menjadi lebih konsisten.

### 6.7 Penyimpanan Ulang Data Bersih

Setelah semua proses pembersihan selesai, data disimpan kembali ke folder seperti:

- `processed`
- `streamlit/eda_outputs`

Format penyimpanan dapat berupa:

- CSV
- JSONL

---

## 7. Proses Pembersihan Khusus pada JSONL

Selain data CSV hasil scraping, proyek ini juga memiliki file JSONL untuk anotasi dan evaluasi agreement.  
Contoh file yang digunakan:

- `apm1_iaaa.jsonl`
- `apm1_iaaa_textcat.jsonl`
- `db_apm1_genap2526_v2.jsonl`

### 7.1 File `apm1_iaaa.jsonl`

File ini berisi ringkasan metrik agreement antar anotator, termasuk:

- `n_examples`
- `n_categories`
- `pairwise_f1`
- `pairwise_precision`
- `pairwise_recall`
- `confusion_matrix`
- `normalized_confusion_matrix`
- `metrics_per_label`

File ini digunakan untuk mengevaluasi kualitas konsistensi anotasi.

### 7.2 File `apm1_iaaa_textcat.jsonl`

File ini menyimpan agreement untuk beberapa label kategori seperti:

- `MANFAAT_POSITIVE`
- `MANFAAT_NEGATIVE`
- `MANFAAT_NEUTRAL`
- `KUALITAS_POSITIVE`
- `KUALITAS_NEGATIVE`
- `KUALITAS_NEUTRAL`

Metrik yang digunakan meliputi:

- `percent_agreement`
- `kripp_alpha`
- `gwet_ac2`

### 7.3 File `db_apm1_genap2526_v2.jsonl`

File ini berisi data anotasi berbasis teks, termasuk:

- teks asli
- token
- spans
- label span
- informasi annotator
- hash input dan task

File ini dianalisis untuk mengetahui:

- panjang teks
- jumlah token
- jumlah span
- distribusi label span
- kombinasi label yang muncul dalam satu record

---

## 8. Ringkasan Hasil EDA

Dari hasil eksplorasi yang tersedia, beberapa temuan utama adalah:

- Data memiliki distribusi teks yang sangat panjang ke kanan, artinya sebagian besar data relatif pendek, tetapi ada beberapa data yang sangat panjang.
- Label `PER-PM`, `ORGANIZATION`, `MEDICAL`, dan `LOCATION` memiliki support yang cukup besar.
- Label `PER-PTG` memiliki support paling kecil sehingga cenderung lebih sulit diprediksi.
- Pada file `apm1_iaaa_textcat.jsonl`, beberapa label menunjukkan agreement tinggi, sehingga lebih aman digunakan dalam dataset bersih.
- Pada data anotasi teks, label span paling sering muncul adalah `PER-PM` dan `MEDICAL`.




