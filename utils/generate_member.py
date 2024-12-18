from faker import Faker
import random
from utils.db_utils import fetch_available_categories


def generate():
    fake = Faker('ko_KR')
    name = fake.name()
    email = fake.email()
    password = fake.password()
    phone = fake.phone_number()
    birthday = fake.date()
    gender = random.choice(['MALE', 'FEMALE'])
    address = fake.address()

    data = {
            'member_id' : email,
            'name': name,
            'email': email,
            'password': password,
            'phone': phone,
            'birthday': birthday,
            'gender': gender,
            'address': address
            }

    return data


def generate_group(memberId):
    # 모임 생성 데이터 생성
    fake = Faker('ko_KR')
    group_name = fake.company()  # 랜덤 모임 이름
    description = fake.catch_phrase()  # 랜덤 설명
    available_categories = fetch_available_categories()
    if not available_categories:
        raise ValueError('사용 가능한 카테고리가 없습니다.')

    num_categories = min(2, len(available_categories))
    categories = random.sample(available_categories, k=num_categories)

    group_data = {
        "memberId": memberId,  # 필수 필드: 사용자 ID
        "groupName": group_name,
        "description": description,
        "categories": categories  # 카테고리 리스트
    }

    print(f"생성된 group_data: {group_data}")
    return group_data