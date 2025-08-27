import argparse
import json
import requests
from datetime import datetime, timedelta

def nik_parse(nik: str):
    provinces = {p['id']: p['name'].upper() for p in requests.get('https://emsifa.github.io/api-wilayah-indonesia/api/provinces.json').json()}
    if len(nik) != 16 or nik[:2] not in provinces:
        raise ValueError('NIK tidak valid: panjang atau kode provinsi salah')

    province_id = nik[:2]
    regencies = {r['id']: r['name'].upper() for r in requests.get(f'https://emsifa.github.io/api-wilayah-indonesia/api/regencies/{province_id}.json').json()}
    if nik[:4] not in regencies:
        raise ValueError('NIK tidak valid: kode kabupaten/kota salah')

    regency_id = nik[:4]
    districts = {d['id'][:-1]: d['name'].upper() for d in requests.get(f'https://emsifa.github.io/api-wilayah-indonesia/api/districts/{regency_id}.json').json()}
    if nik[:6] not in districts:
        raise ValueError('NIK tidak valid: kode kecamatan salah')

    province = provinces[province_id]
    city = regencies[regency_id]
    subdistrict = districts[nik[:6]]
    day = int(nik[6:8])
    month = int(nik[8:10])
    year_code = nik[10:12]
    uniq_code = nik[12:16]

    gender = 'PEREMPUAN' if day > 40 else 'LAKI-LAKI'
    birth_day = day - 40 if day > 40 else day
    current_year = datetime.now().year % 100
    birth_year = int(f"20{year_code}") if int(year_code) <= current_year else int(f"19{year_code}")
    birth_date = datetime(birth_year, month, birth_day)
    today = datetime.now()

    years = today.year - birth_date.year
    months = today.month - birth_date.month
    days = today.day - birth_date.day
    if days < 0:
        days += (birth_date.replace(month=birth_date.month + 1, day=1) - timedelta(days=1)).day
        months -= 1
    if months < 0:
        months += 12
        years -= 1
    age = f"{years} Tahun {months} Bulan {days} Hari"

    if years < 12:
        age_category = 'Anak-anak'
    elif years < 18:
        age_category = 'Remaja'
    elif years < 60:
        age_category = 'Dewasa'
    else:
        age_category = 'Lansia'

    next_birthday_year = today.year if (today.month, today.day) < (month, birth_day) else today.year + 1
    next_birthday = datetime(next_birthday_year, month, birth_day)
    diff = next_birthday - today
    months_left = diff.days // 30
    days_left = diff.days % 30
    birthday_countdown = f"{months_left} Bulan {days_left} Hari"

    regency_type = 'Kota' if 'KOTA' in city else 'Kabupaten'
    area_code = f"{province_id}.{regency_id[2:]}.{nik[4:6]}"

    return {
        "nik": nik,
        "identitas": {
            "kelamin": gender,
            "tanggal_lahir": birth_date.strftime("%d/%m/%Y"),
            "umur": {
                "detail": age,
                "kategori": age_category,
                "ulang_tahun_berikutnya": f"{birthday_countdown} lagi"
            }
        },
        "wilayah": {
            "provinsi": {"kode": province_id, "nama": province},
            "kabupaten_kota": {"kode": regency_id, "nama": city, "jenis": regency_type},
            "kecamatan": {"kode": nik[:6], "nama": subdistrict},
            "kode_wilayah": area_code
        },
        "nomor_urut": uniq_code
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--nik", required=True, help="Nomor Induk Kependudukan (16 digit)")
    args = parser.parse_args()

    try:
        data = nik_parse(args.nik)
        print(json.dumps(data, indent=4, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({"error": str(e)}, indent=4, ensure_ascii=False))
