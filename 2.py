import random
import mysql.connector
import requests
from utils.db_config import DB_CONFIG
from utils.generate_member import generate, generate_group

api = 'http://tr-sv-1:9090/api/v1'

session = requests.Session()

# 회원 가입 또는 로그인에서 받아오는 Response에서 member의 id를 추출 후 고정된 memberId를 사용
memberId = None


# 1. 로그인
def login(email=None, password=None):
    connection = None  # connection 변수를 초기화
    try:
        if not email or not password:
            # 데이터베이스 연결 시도
            connection = mysql.connector.connect(
                host=DB_CONFIG['host'],
                port=DB_CONFIG['port'],
                user=DB_CONFIG['user'],
                password=DB_CONFIG['password'],
                database=DB_CONFIG['database']
            )
            cursor = connection.cursor(dictionary=True)

            # 데이터베이스에서 랜덤으로 사용자 선택
            cursor.execute("SELECT id, email, password FROM member ORDER BY RAND() LIMIT 1")
            user = cursor.fetchone()

            # 사용자가 없으면 로그인 실패 처리
            if not user:
                print("사용자를 찾을 수 없습니다.")
                return False

            # 사용자 이메일과 비밀번호 추출
            email, password = user['email'], user['password']
            # memberId = user['id']

        # API를 통해 로그인 요청
        response = session.put(api + '/member/login', json={'email': email, 'password': password})

        if response.status_code == 200:
            print(f"로그인 성공: {email}, memberId: {response.json()['id']}")
            # return memberId
            return response.json()

        else:
            print(f"로그인 실패: {email}")
            return False
    except mysql.connector.Error as err:
        # 데이터베이스 에러 발생 시 로그 출력
        print(f"DB 에러 발생: {err}")
        return False
    finally:
        # connection이 초기화된 경우에만 닫기 시도
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

    response = session.get(api + '/member/login', params={'email': email, 'password': password})
    if not response.status_code == 200:
        return False


# 2. 가입된 모임 목록 확인
def get_my_groups(member_id):
    response = session.get(api + '/group/my', params={'memberId': member_id})
    if response.status_code == 200:
        groups = response.json()
        print(f"가입된 모임 목록: {groups}")
        return groups
    else:
        print(f"모임 목록 조회 실패: {response.status_code}, {response.text}")
        return []


# 3. 게시판 확인
def get_group_board(group_id):
    response = session.get(api + '/group/board', params={'groupId': group_id})
    if response.status_code == 200:
        posts = response.json()
        print(f"모임 게시판 최신 글: {posts}")
        return posts
    else:
        print(f"게시판 조회 실패: {response.status_code}, {response.text}")
        return []

# 4. 게시판 댓글 작성
def post_comment(board_id, member_id):
    response = session.post(api + '/group/comment', json={'boardId': board_id, 'memberId': member_id})
    if response.status_code == 201:
        print(f"댓글 작성 완료: {response.json()}")
    else:
        print(f"댓글 작성 실패: {response.status_code}, {response.text}")


# 5. 여행 계획 결정 (게시판에 글 작성)
def travle_plan(group_id, member_id):
    response = session.post(api + '/group/board', json={'groupId': group_id, 'memberId': member_id})
    if response.status_code == 201:
        print(f"여행 계획 게시 완료: {response.json()}")
    else:
        print(f"여행 계획 게시 실패: {response.status_code}, {response.text}")


# 6. 리뷰 작성
def post_review(group_id, member_id):
    response = session.post(api + '/group/board', json={'groupId': group_id, 'memberId': member_id})
    if response.status_code == 201:
        print(f"여행 리뷰 작성 완료: {response.json()}")
    else:
        print(f"여행 리뷰 작성 실패: {response.status_code}, {response.text}")



if __name__ == '__main__':
    print("==시나리오 시작==")

    # 시나리오 랜덤으로 돌리기
    choice_num = random.choice([1, 2, 3, 4, 5, 6])
    print(f"선택된 시나리오 번호:")