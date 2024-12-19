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


# 2-1. 가입된 모임이 없을 경우
def get_random_group():
    try:
        # 데이터베이스 연결 시도
        connection = mysql.connector.connect(
            host=DB_CONFIG['host'],
            port=DB_CONFIG['port'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password'],
            database=DB_CONFIG['database']
        )
        cursor = connection.cursor(dictionary=True)

        # 랜덤으로 모임 가져오기
        cursor.execute("SELECT group_id, group_name FROM groups ORDER BY RAND() LIMIT 1")
        group = cursor.fetchone()

        if group:
            print(f"랜덤으로 선택된 모임: {group['group_name']}")
        else:
            print("랜덤으로 선택된 모임이 없습니다.")
        return group
    except mysql.connector.Error as err:
        print(f"DB 에러 발생: {err}")
        return None
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


# 3. 게시판 확인
def get_group_board(group_id):
    response = session.get(api + '/posts', params={'groupId': group_id})
    if response.status_code == 200:
        posts = response.json()
        print(f"모임 게시판 최신 글: {posts}")
        return posts
    else:
        print(f"게시판 조회 실패: {response.status_code}, {response.text}")
        return []

# 3-1. 게시판에 글 없을 경우 여행 계획 글 작성
def create_travle_post(group_id, member_id, title="여행 계획"):
    post_data = {
        "groupId": group_id,
        "memberId": member_id,
        "title": title,
        "contentType": "text",
        "content": ""
    }
    response = session.post(api + '/group/post', json=post_data)
    if response.status_code == 201:
        print(f"여행 계획 글 작성 완료: {response.json()}")
        return response.json()
    else:
        print(f"여행 계획 글 작성 실패: {response.status_code}, {response.text}")
        return None

# 4. 게시판 댓글 작성
def post_comment(board_id, member_id):
    response = session.post(api + '/group/comment', json={'boardId': board_id, 'memberId': member_id})
    if response.status_code == 201:
        print(f"댓글 작성 완료: {response.json()}")
    else:
        print(f"댓글 작성 실패: {response.status_code}, {response.text}")


# 5. 여행 계획 결정 (게시판에 글 작성)
def travle_plan(group_id, member_id):
    response = session.post(api + '/group/notice', json={'groupId': group_id, 'memberId': member_id})
    if response.status_code == 201:
        print(f"여행 계획 게시 완료: {response.json()}")
    else:
        print(f"여행 계획 게시 실패: {response.status_code}, {response.text}")


# 6. 리뷰 작성
def post_review(group_id, member_id):
    response = session.post(api + '/postComment', json={'groupId': group_id, 'memberId': member_id})
    if response.status_code == 201:
        print(f"여행 리뷰 작성 완료: {response.json()}")
    else:
        print(f"여행 리뷰 작성 실패: {response.status_code}, {response.text}")



if __name__ == '__main__':
    print("==시나리오 시작==")

    # 1. 로그인
    login_response = login()
    if not login_response:
        print("로그인 실패: 프로세스를 중단합니다.")
        exit()

    member_id = login_response.get('email')
    if not member_id:
        print("로그인 응답에 'id'가 없습니다. 응답:", login_response)
        exit()

    print(f"로그인한 사용자 ID: {member_id}")

    # 2. 가입된 모임 목록 확인 또는 랜덤 모임 가져오기

    print("\n=== 가입된 모임 목록 확인 ===")
    groups = get_my_groups(member_id)

    if not groups:
        print("가입된 모임이 없습니다. DB에서 랜덤으로 모임을 가져옵니다.")
        selected_group = get_random_group()
        if not selected_group:
            print("랜덤으로 선택된 모임이 없습니다. 시나리오를 종료합니다.")
            exit()

    else:
        # 가입된 모임에서 랜덤으로 하나 선택
        selected_group = random.choice(groups)

    group_id = selected_group.get('group_id') or selected_group.get('id')
    if not group_id:
        print("모임 ID를 가져올 수 없습니다. 선택된 모임 데이터", selected_group)
        exit()

    print(f"선택된 모임 ID: {group_id}, 모임 이름: {selected_group['group_id']}")


    # 3. 게시판 확인
    print("\n=== 게시판 확인 ===")
    posts = get_group_board(group_id)

    if not posts:
        print("게시판에 글이 없습니다. 여행 계획 글을 작성합니다.")

        # 3-1. 게시판에 여행 계획 글 작성
        print("\n=== 게시판에 여행 계획 글 작성 ===")
        created_post = create_travle_post(group_id, member_id)

        if created_post:
            # 새로 작성된 글을 posts 리스트에 추가
            posts = [created_post]

        else:
            print("여행 계획 글 작성 실패로 게시판 작업을 중단합니다.")

    # 게시판 글이 없을 경우 처리
    if not posts:
        print("여행 계획 글 작성 후에도 게시판에 글이 없습니다. 시나리오를 종료합니다.")
        exit()

    # 게시판에서 첫 번째 글 사용
    first_post = posts[0]
    board_id = first_post['id']
    print(f"게시판 글 ID: {board_id}, 제목: {first_post['title']}")

    # 4. 게시판 댓글 작성
    print("\n=== 게시판 댓글 작성 ===")
    post_comment(board_id, member_id)

    # 5. 여행 계획 결정
    print("\n=== 여행 계획 결정===")
    travle_plan(group_id, member_id)

    # 6. 리뷰 작성
    print("\n=== 리뷰 작성===")
    post_review(group_id, member_id)

    print("\n=== 시나리오 종료===")