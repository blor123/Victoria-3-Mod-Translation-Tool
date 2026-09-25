[English](README.md) | [한국어](README_KO.md)

# Victoria 3 Mod Translation Tool & Manager (V3MM)

**Victoria 3 Mod Translation Tool & Manager (V3MM)**은 Victoria 3 모드의 localization 번역과 관리를 편리하게 하기 위한 Windows 프로그램입니다.

V3MM은 AI/ChatGPT 번역을 위해 localization 파일을 ZIP 패키지로 준비하고, 번역 완료 후 ZIP을 다시 불러와 모드에 적용할 수 있는 파일 기반 작업 흐름을 제공합니다. V3MM 자체가 파일을 자동 번역하거나 OpenAI API 또는 ChatGPT API에 직접 연결되는 방식은 아닙니다.

[최신 버전 다운로드](https://github.com/blor123/Victoria-3-Mod-Translation-Tool/releases/latest)

![V3MM 인터페이스](https://github.com/user-attachments/assets/f30cfdd2-c88c-467d-8b99-702e565ffe8e)

## 주요 기능

### 번역 패키지 생성 (Translation Package)

Victoria 3 localization 파일을 번역용으로 준비합니다.

- 개별 YML 파일, 여러 YML 파일 또는 localization 파일이 포함된 폴더 선택
- Victoria 3의 `localization/korean` 폴더 구조 유지
- 필요한 경우 `_english.yml` 파일명을 `_korean.yml`로 변환
- 원본 파일을 보존하면서 ZIP 복사본의 `l_english:` 선언을 `l_korean:`으로 변경
- 번역 대상 YML 파일 미리보기 및 중복 선택 제거
- 번역용 ZIP 패키지 생성
- 제공되는 번역 지침 확인, 편집, 초기화 및 복사

### 번역 적용 (Apply Translation)

번역이 완료된 파일을 불러와 적용합니다.

- 압축 파일 이름이나 최상위 래퍼 폴더 이름과 관계없이 번역 ZIP 불러오기
- 번역된 localization 파일 자동 탐색
- 안전하지 않은 경로와 지원하지 않는 압축 파일을 차단하는 안전한 ZIP 압축 해제
- 적용 전에 중복 대상 감지
- 설치 대상 파일 미리보기
- 기존 파일 교체 전 백업 생성
- 파일이 이미 존재할 경우 백업 후 덮어쓰기, 덮어쓰기, 건너뛰기 또는 취소 선택

### 다국어 UI

V3MM은 다음 UI 언어를 지원합니다.

- 한국어
- English
- 简体中文
- 繁體中文
- 日本語

선택한 UI 언어는 저장되며 V3MM을 다시 실행할 때 유지됩니다.

## ChatGPT 번역 방식

V3MM은 **OpenAI API 또는 ChatGPT API에 직접 연결되지 않습니다.** OpenAI API Key, ChatGPT 로그인 정보, 쿠키 또는 세션 토큰을 요구하거나 저장하지 않습니다.

기본 작업 흐름은 다음과 같습니다.

1. V3MM에서 Victoria 3 localization 파일을 선택합니다.
2. 번역 패키지를 생성합니다.
3. 생성된 ZIP을 ChatGPT에 업로드합니다.
4. V3MM에서 제공하는 번역 지침을 이용해 번역합니다.
5. 번역된 ZIP을 다운로드합니다.
6. V3MM에서 ZIP을 다시 불러옵니다.
7. 적용할 파일을 확인한 뒤 번역된 파일을 적용합니다.

기존 ChatGPT 환경을 이용할 수 있으므로 별도의 OpenAI API Key를 준비할 필요가 없습니다.

## 설치 방법

V3MM은 **Windows 10** 및 **Windows 11**을 지원합니다.

1. [Releases 페이지](https://github.com/blor123/Victoria-3-Mod-Translation-Tool/releases)를 엽니다.
2. 최신 Release를 선택합니다.
3. **Assets**에서 패키징된 `.exe` 파일을 다운로드합니다.
4. 다운로드한 파일을 실행합니다.

패키징된 실행 파일에는 필요한 런타임이 포함되어 있으므로 Python을 별도로 설치할 필요가 없습니다.

> 중요한 모드 파일은 별도로 백업해 두는 것을 권장합니다. V3MM은 백업과 안전한 압축 해제 기능을 제공하지만, 모드마다 파일 구조가 다를 수 있습니다.

## Roadmap

### 현재 버전: v1.2.0

- 번역 패키지 생성 및 번역 적용 화면 개선
- 파일 및 폴더 드래그 앤 드롭
- localization 언어 선언 처리
- 번역 지침 관리
- 다국어 UI
- 번역 대상 미리보기 및 패키지 요약
- 기존 안전 검사, 중복 감지 및 백업 선택 기능 유지

### 향후 계획

다음 기능은 향후 계획이며 현재 지원되는 기능이 아닙니다.

- 번역 검증
- 번역 프로젝트 관리
- 모드 충돌 분석
- 모드 로드 순서 분석 및 추천
- 업데이트 시스템

개발 진행 상황에 따라 Roadmap은 변경될 수 있습니다.

## 제작자

**Created by KakaoL**

Steam Profile: [https://steamcommunity.com/id/KakaoLV3MM/](https://steamcommunity.com/id/KakaoLV3MM/)
