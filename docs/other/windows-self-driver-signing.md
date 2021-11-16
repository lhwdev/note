---
title: 윈도우에서 직접 드라이버 서명하기
date: 2021-11-16
---


# 윈도우에서 직접 드라이버 서명하기


!!! warning "**작성 중**"
    이 글은 아직 완성되지 않았어요.
    사실 그 이유는 지금 저 짓을 하고 있어서...

## 왜?
내가 온라인 수업을 하면서 마이크로 장난(...)을 좀 쳐보고 싶어졌다. 그리고 평소에 음악을 들을 때
FL 같은 DAW로 소리를 직접 보정해서 들었는데, 오디오 스펙트럼을 보면 좀 간지나기 때문에였다...

아무튼 이러한 짓거리에는 필수적으로 필요했던 게 바로 가상 오디오 장치였다. 이미 나와있는 것들은
아래와 같았는데, 모두 만족스럽지 않았다.

- **VB Audio Cable**  
  무료 체험판의 경우 케이블 1개만 사용 가능.
  `온라인 수업을 하며 마이크로 장난`과 `음악 보정` 둘 다 하려면 케이블이 적어도 2개는 있어야 했다.

- **ODeus ASIO Link Pro**  
  ... 그냥 이거 쓸까?  
  디자인이 마음에 안들었다.

- **Virtual Audio Cable**  
  엄청 좋아보이는데 유료임.

그러다가 Synchronous Audio Router(SAR)이라는 프로그램을 발견했다. 사실 오디오를 라우팅하거나 보정하는 거는 FL로 하면 되기
때문에 전혀 문제가 되지 않았다. SAR은

- 동적으로 가상 오디오 장치 추가 (무제한! 그냥 윈도우가 버텨주는 한 계속 만들 수 있음)
- 무료, 오픈소스임
- 그냥 마음에 듦
- 성능이 좋은 편임

이러했고, 그래서 SAR을 설치하기로 마음을 먹었는데...

> ## Unsigned prereleased drivers note
> Prereleases of SAR are unsigned. That means that it is required to enable testsigning boot option
  to make Windows load the driver. Else the driver won't be loaded.

이 시점에, 나는 UEFI 설정에서 Secure Boot를 켜놨었고 곧 윈도우 11로 업그레이드할 계획이었다.
그리고 보안을 고려하기도 했기 때문에 `testsigning` 부트 설정을 켜는 건 가능한 선택이 아니었다.

그러다가 [어느 한 이슈](https://github.com/eiz/SynchronousAudioRouter/issues/86)를 보게 되었다.
> UPDATE 3: SUCCESS!!!!!!!!! I am running the latest SAR in Reaper as we speak on windows 10 without testmode.

어떤 사람이 성공했다고 한다. 그래서 나도 해보기로 했다. ㅋㅋㅋㅋㅋㅋㅋㅋ
벌써부터 험난해보인다.


## 본격적으로 시작
내가 참조한 문서들은 저기 말한 '어느 한 이슈'에 설명되어 있는 방법이었다. 설명이 아주 불친절했다. 실제로
불친절한지는 모르겠지만 (하지만 `its confusing and you have to jump back and forth between his guide and an older one` 라는 말이 있다)
내가 한국인이란 점을 감안하면..
