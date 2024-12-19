import random
from faker import Faker
import mysql.connector
import requests
from utils.db_config import DB_CONFIG

api = 'http://tr-sv-1:9090/api/v1'

session = requests.Session()
fake = Faker('ko_KR')

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

        # API를 통해 로그인 요청
        response = session.put(api + '/member/login', json={'email': email, 'password': password})

        if response.status_code == 200:
            print(f"로그인 성공: {email}, memberId: {response.json()['id']}")
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
    print(f"get_my_groups 호출: memberId={member_id}")  # 디버깅 로그
    response = session.get(api + '/group/my', params={'memberId': member_id})
    if response.status_code == 200:
        groups_response = response.json()
        groups = groups_response.get('content', [])  # 'content'에서 실제 모임 목록 가져오기
        if groups:
            print("가입된 모임 목록:")
            for group in groups:
                print(f"- {group.get('groupName', '이름 없음')} (ID: {group.get('id')})")
        else:
            print("가입된 모임이 없습니다.")
        return groups_response
    else:
        print(f"모임 목록 조회 실패: {response.status_code}, {response.text}")
        return {'content': []}


# 3. 내 모임 중 랜덤으로 선택
def choose_random_group(member_id):
    groups_response = get_my_groups(member_id)
    groups = groups_response.get('content', [])  # 'content' 키에서 실제 모임 목록 가져오기
    if not groups:
        print("가입된 모임이 없습니다.")
        return None
    chosen_group = random.choice(groups)
    print(f"선택된 모임: {chosen_group}")
    return chosen_group


# 4. 선택된 모임의 게시판 확인
def get_group_board(group_id):
    response = session.get(api + '/posts', params={'groupId': group_id})
    if response.status_code == 200:
        data = response.json()

        posts = data.get('posts') if isinstance(data, dict) else data
        if isinstance(posts, list):
            print(f"모임 게시판 글 목록: {posts}")
            return posts
    else:
        print(f"게시판 조회 실패: {response.status_code}, {response.text}")
        return []


def generate_random_text():
    title = " ".join([fake.catch_phrase() for _ in range(1)])
    content = " ".join([fake.catch_phrase() for _ in range(5)])
    return title, content

def generate_random_comment():
    comment = " ".join([fake.catch_phrase() for _ in range(2)])
    return comment

# 5. 게시판에 글 작성
def create_travle_post(group_id, member_id):
    title, content = generate_random_text()
    post_data = {
        "title": title,
        "content": content,
        "type": "COMMON"
    }

    params = {
        "memberId": member_id,
        "groupId": group_id
    }
    response = session.post(api + '/group/post', params=params, json=post_data)
    if response.status_code == 201:
        print(f"여행 계획 글 작성 완료: {response.json()}")
        return {"postId": response.json().get("postId"), "title": title, "content": content}
    else:
        print(f"여행 계획 글 작성 실패: {response.status_code}, {response.text}")
        return None


# 6. 게시판 글에 댓글 작성
def post_comment(post_id, group_id, member_id, content=None):
    if content is None:
        content = generate_random_comment()  # 댓글 내용이 없으면 랜덤 생성

    comment_data = {
        "memberId": member_id,
        "groupId": group_id,
        "postId": post_id,
        "content": content
    }

    response = session.post(f"{api}/postComment", json=comment_data)
    if response.status_code == 201:
        print(f"댓글 작성 완료: {response.json()}")
        return {"commentId": response.json().get("postId"), "content": content}
    else:
        print(f"댓글 작성 실패: {response.status_code}, {response.text}")
        return None


if __name__ == '__main__':
    print("==시나리오 시작==")

    # 1. 로그인
    login_response = login()
    if not login_response:
        print("로그인 실패: 프로세스를 중단합니다.")
        exit()

    member_id = login_response.get('id')
    if not member_id:
        print("로그인 응답에 'id'가 없습니다. 응답:", login_response)
        exit()

    print(f"로그인한 사용자 ID: {member_id}")

    # 2. 가입된 모임 목록 확인
    print("\n=== 가입된 모임 목록 확인 ===")
    groups = get_my_groups(member_id)
    if not groups:
        print("가입된 모임이 없습니다. 시나리오를 종료합니다.")
        exit()

    # 3. 내 모임 중 랜덤으로 선택
    print("\n=== 가입된 모임 랜덤 선택 ===")
    chosen_group = choose_random_group(member_id)
    if not chosen_group:
        print("모임 선택 실패. 시나리오를 종료합니다.")
        exit()

    group_id = chosen_group.get('id')
    print(f"선택된 모임 ID: {group_id}")

    # 4. 선택된 모임의 게시판 확인
    print("\n=== 게시판 확인 ===")
    board_posts = get_group_board(group_id)
    if not board_posts:
        print("게시판에 글이 없습니다. 여행 계획 글을 작성합니다.")

        # 5. 게시판에 글 작성
        print("\n=== 게시판에 글 작성 ===")
        new_post = create_travle_post(group_id, member_id)
        if not new_post:
            print("게시판 글 작성 실패. 시나리오를 종료합니다.")
            exit()

        post_id = new_post.get('postId')
        post_title = new_post.get('title')
        post_content = new_post.get('content')
        print(f"게시판에 작성된 글 ID: {post_id}")
        print(f"작성된 글 제목: {post_title}")
        print(f"작성된 글 내용: {post_content}")

    else:
        # 게시판에서 첫 번째 글 사용
        first_post = board_posts[0]
        post_id = first_post.get('id')
        print(f"기존 게시판 글 ID: {post_id}")

    # 6. 게시판 글에 댓글 작성
    print("\n=== 댓글 작성 ===")
    comment_response = post_comment(post_id, group_id, member_id)
    if not comment_response:
        print("댓글 작성 실패. 시나리오를 종료합니다.")
        exit()

    comment_content = comment_response.get('content')
    print(f"작성된 댓글 내용: {comment_content}")

    print("\n=== 시나리오 종료 ===")

