import os
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def setup_directories():
    """디버깅 및 기타 필요 디렉토리 생성"""
    directories = [
        'data',
        'downloads',
        'reports',
        'index',
        'debug',
        'debug/kdi',
        'debug/bok'
    ]
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            logging.info(f"디렉토리 생성: {directory}")
        else:
            logging.info(f"디렉토리 이미 존재함: {directory}")

if __name__ == "__main__":
    setup_directories()
    logging.info("모든 디렉토리 생성 완료")
