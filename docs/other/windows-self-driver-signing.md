---
title: 윈도우에서 직접 드라이버 서명하기
date: 2021-11-16
---


# 윈도우에서 직접 드라이버 서명하기


!!! warning "**안내**"
    이 글을 따라하기 전에 충분히 찾아보고 하세요.
    필자는 어떤 문제도 보장하지 않습니다.

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


## 본격적으로 시작!
내가 참조한 문서들은 저기 말한 '어느 한 이슈'에 설명되어 있는 방법이었다. 설명이 아주 불친절했다.
실제로 불친절한지는 모르겠지만 (하지만 `its confusing and you have to jump back and forth between his guide and an older one` 라는 말이 있었다)
내가 한국인이란 점을 감안하면..

시작하기 전에 자신의 기기에서 **UEFI 플랫폼 키**를 설정하는 방법이 있는지, 어떻게 하는지를 미리
알아보자. UEFI가 지원하지 않는다면 이걸 할 수가 없다.

!!! info 일단 이걸 하기 전에 위에 참조한 이슈랑
[거기서 참조하는 이 리포](https://github.com/valinet/ssde)는 한번 훑어보시는 걸 추천드립니다.

## 인증서 만들기
인증서를 만드는 방법은 [이 문서에 잘 설명되어 있다](https://github.com/HyperSine/Windows10-CustomKernelSigners/blob/master/asset/build-your-own-pki.md).
하지만 혹시나 필요한 사람이 있을까봐 한국어로 번역하고 설명을 추가해봤다.

우리가 할 것은 이 기기에서 작동하는 인증서를 만드는 것인데, 이 기기에서만 작동하는 '가상의 인증서 키
발급 기관' 같은 걸 만든 다음 그 기관의 인증서를 이용해서 **UEFI 플랫폼 키 인증서**와
**커널 모드 드라이버 인증서**를 만들 것이다.

**일단 powershell을 관리자 모드로 열고, 닫지 말고 계속 켜놓아야 한다.**

### '인증서 발급 기관' (Root CA Certificate) 생성
어떤 Root CA 자체의 인증서가 신뢰된다면 그 CA가 발급한 다른 인증서도 마천가지로 신뢰될 것이다.
예를 들어 WIZVERA라는 CA 인증기관을 믿을 수 있다면, 그 인증기관에서 발급한 인증서도 믿을 수 있다.
그래서 우리가 HTTPS 서명을 만들려면 어떤 인증서 발급기관에서 돈을 주고(물론 무료도 있다) 인증서를
발급받는 것이다.

아래 명령어를 실행해라.
``` powershell
$cert_params = @{
    Type = 'Custom'
    Subject = 'CN=Localhost Root Certification Authority'
    FriendlyName = 'Localhost Root Certification Authority'
    TextExtension = '2.5.29.19={text}CA=1'
    HashAlgorithm = 'sha512'
    KeyLength = 4096
    KeyAlgorithm = 'RSA'
    KeyUsage = 'CertSign','CRLSign'
    KeyExportPolicy = 'Exportable'
    NotAfter = (Get-Date).AddYears(100)
    CertStoreLocation = 'Cert:\LocalMachine\My'
}

$root_cert = New-SelfSignedCertificate @cert_params
```

- `#!powershell (Get-Date).AddYears(100)`: 100년 대신 다른 원하는 값을 입력해도 된다.
- `#!powershell TextExtension = '2.5.29.19={text}CA=1'`:
  - `2.5.29.19`는 [`Basic Constraints`를 나타내는 OID이다](https://www.alvestrand.no/objectid/2.5.29.19.html).
    즉, 이 인증서를 발급한 주체가 CA로 작용할 수 있다는 것이다.
  - `CA=1`은 이 인증서가 CA 인증서라는 것이다.
  - `&pathlength=x`를 넣는다면 이 CA가 발급한 인증서로 인증서를 발급하고, 그걸로 또 인증서를
    발급할 수 있는지, 얼마나 발급할 수 있는지를 말해준다. 필요하면 원문을 참고해라.

이 명령어를 실행한 후 `certlm.msc`를 실행해서 `개인용/인증서` 또는 `Personal\Certificates`에
새롭게 발급한 비밀키가 포함된 인증서 1(이름이 `Localhost Root Certification Authority`인 것)을
확인할 수 있다.  
그리고 `중간 인증 기관/인증서` 또는 `Intermediate Certification Authority\Certificates`에서
비밀키 없이 공개키만 있는 인증서 2(이름이 마천가지)를 확인할 수 있다. 이 '인증서 2'를
`신뢰할 수 있는 루트 인증/인증서`(또는 `Trusted Root Certification Authority\Certificates`)로
드래그해서 옮긴다. 그럼 인증서 1과 인증서 2 모두가 인증되었다고 뜬다.


