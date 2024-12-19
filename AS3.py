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

# 3. 내 글 및 댓글 확인
def check_user_activity(member_id, group_id):
    print(f"check_user_activity 호출: memberId={member_id}, groupId={group_id}")

    # 게시글 확인
    response_posts = session.get(api + '/posts', params={'groupId': group_id, 'memberId': member_id})
    if response_posts.status_code == 200:
        posts = response_posts.json().get('posts', [])
        post_count = len(posts)
        print(f"모임 {group_id} - 내 게시글 수: {post_count}")
    else:
        print(f"모임 {group_id} - 게시글 확인 실패: {response_posts.status_code}, {response_posts.text}")
        return 0, 0

    # 댓글 확인
    response_comments = session.get(api + '/postComments', params={'memberId': member_id, 'groupId': group_id})
    if response_comments.status_code == 200:
        comments = response_comments.json().get('comments', [])
        comment_count = len(comments)
        print(f"모임 {group_id} - 내 댓글 수: {comment_count}")
    else:
        print(f"모임 {group_id} - 댓글 확인 실패: {response_comments.status_code}, {response_comments.text}")
        return post_count, 0

    return post_count, comment_count

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
    groups_content = groups.get('content', [])
    if not groups_content:
        print("가입된 모임이 없습니다. 시나리오를 종료합니다.")
        exit()

    # 모든 모임에서 게시글 및 댓글 카운트
    total_posts = 0
    total_comments = 0

    for group in groups_content:
        group_id = group.get('id')
        group_name = group.get('groupName', '이름 없음')
        print(f"\n모임 ID: {group_id}, 이름: {group_name}")

        # 3. 내 글 및 댓글 확인
        print("\n=== 내 글 및 댓글 확인 ===")
        post_count, comment_count = check_user_activity(member_id, group_id)
        total_posts += post_count
        total_comments += comment_count

    print(f"\n총 게시글 수: {total_posts}")
    print(f"총 댓글 수: {total_comments}")

    print("\n=== 시나리오 종료 ===")


