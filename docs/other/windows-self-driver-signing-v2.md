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
    나중에 성공하면 스크립트로도 만들어서 배포할게요

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
내가 참조한 문서들은 저기 말한 '어느 한 이슈'에 설명되어 있는 방법을 변형해서 OpenSSL을 쓴
방법이었다. 설명이 아주 불친절했다.
실제로 불친절한지는 모르겠지만 (하지만 `its confusing and you have to jump back and forth between his guide and an older one` 라는 말이 있었다)
내가 한국인이란 점을 감안하면..

시작하기 전에 자신의 기기에서 **UEFI 플랫폼 키**를 설정하는 방법이 있는지, 어떻게 하는지를 미리
알아보자. UEFI가 지원하지 않는다면 이걸 할 수가 없다.

!!! info "**참고**"
    일단 이걸 하기 전에 위에 참조한 이슈랑
    [거기서 참조하는 이 리포](https://github.com/valinet/ssde)는 한번 훑어보시는 걸 추천드립니다.

## 인증서 만들기
인증서를 만드는 방법은 [이 문서에 잘 설명되어 있다](https://github.com/HyperSine/Windows10-CustomKernelSigners/blob/master/asset/build-your-own-pki.md).
하지만 저 방법대로 했더니 내 UEFI(Dell임)가 인증서를 뱉길래 OpenSSL을 써서 다시 시도해보았다.

우리가 할 것은 이 기기에서 작동하는 인증서를 만드는 것인데, 이 기기에서만 작동하는 '가상의 인증서 키
발급 기관' 같은 걸 만든 다음 그 기관의 인증서를 이용해서 **UEFI 플랫폼 키 인증서**와
**커널 모드 드라이버 인증서**를 만들 것이다.
참고로 윈도우 11에서도 잘 된다고 한다.

**'인증서 만들기'를 하는 동안 powershell/cmd를 관리자 모드로 열어야 한다.**
이 글은 파워셸을 기준으로 설명한다. cmd라면 알아서 바꾸시길... (예를 들어 줄 끝에 `\``가 있다면
그걸 지우고 다음줄과 합치면 된다.)

아래의 지시사항을 다 따른다면 아래와 같은 파일 구조가 만들어진다.
``` markdown
localhost-ca
- private.key
- cert-request.conf
- cert-request.csr
- cert.cer

```

### OpenSSL 설치
깃을 설치할 때 기본값으로 OpenSSL이 번들되어 있는데, 그걸 쓰고싶다면
[이 StackOverflow 답변](https://stackoverflow.com/a/51757939/10744716)을 참고하자.

나는 걍 깔고 싶어서 걍 깔았다.
Chocolatey가 깔려있는 사람이라면 관리자 권한 셸에서 `#!powershell choco install openssl`을 치기만 하면
된다. 터미널을 껐다 켜기 싫으면 `#!powershell refreshenv`만 치면 된다.


### '인증서 발급 기관' (Root CA Certificate) 생성
어떤 Root CA 자체의 인증서가 신뢰된다면 그 CA가 발급한 다른 인증서도 마천가지로 신뢰될 것이다.
예를 들어 WIZVERA라는 CA 인증기관을 믿을 수 있다면, 그 인증기관에서 발급한 인증서도 믿을 수 있다.
그래서 우리가 HTTPS 서명을 만들려면 어떤 인증서 발급기관에서 돈을 주고(물론 무료도 있다) 인증서를
발급받는 것이다.


`localhost-ca` 폴더를 만들고 아래 명령어를 실행해라.
``` powershell
cd localhost-ca

# 비공개 키 생성하기
openssl genrsa -aes256 -out private.key 2048
```
이 명령어를 설명해보자면,

- `-aes256`: 생성되는 비공개 키를 암호화해서 보관한다. 즉 암호를 암호화하는 옵션인 것이다. 비밀번호를
  입력하는 게 귀찮다면 생략해도 되긴 한데 가능하면 설정하자.
- `-out private.key`: 'private.key'라는 파일로 내보낸다.
- `2048`: 키의 길이를 2048비트로 한다.


그 다음, 아래 내용을 복붙한 후 원하는 내용은 수정하고 `cert-request.conf`이라는 이름으로 저장하자.
```
[ req ]
default_bits = 2048
default_md = sha256
default_keyfile = private.key
distinguished_name = localhost_root_ca
extensions = v3_ca
req_extensions = v3_ca

[ v3_ca ]
basicConstraints = critical, CA:TRUE, pathlen:0
subjectKeyIdentifier = hash
keyUsage = keyCertSign, cRLSign
nsCertType = sslCA, emailCA, objCA

[ localhost_root_ca ]
countryName_default = 

# 기관
organizationName_default = Localhost

# 기관 부서
organizationalUnitName_default  = 

# 이 인증서의 이름
commonName_default = Localhost Root Certification Authority
```

터미널로 돌아와서 아래 명령어를 입력하자.
``` powershell
openssl req -new -key private.key -out cert-request.csr -config cert-request.conf
```

아래처럼 뜰 것이다.
```
Enter pass phrase for private.key:
You are about to be asked to enter information that will be incorporated
into your certificate request.
What you are about to enter is what is called a Distinguished Name or a DN.
There are quite a few fields but you can leave some blank
For some fields there will be a default value,
If you enter '.', the field will be left blank.
-----
Country Name (2 letter code) []:
Organization Name (eg, company) [Localhost]:
Organizational Unit Name (eg, section) []:
Common Name (eg, your name or your server's hostname) [Localhost Root Certification Authority]:
```
비밀번호를 입력하고, 나머지는 `cert-request.conf` 파일에서 설정했기 때문에 엔터를 연타해주면 자동으로 넘어간다.

그럼 `cert-request.csr` 파일이 생겼을 것이다. 아래의 명령어로 실제 인증서를 만들어주자.
```powershell
openssl x509 -req -days 18250 -extensions v3_ca `
  -in cert-request.csr -signkey private.key `
  -out cert.cer -extfile cert-request.conf
```

- `-days 18250`에서 18250을 원하는 날짜로 수정해주면 된다. 18250일은 약 10년이다. (정확하게는 265 * 10)
- `-extensions v3_ca`는 이게 CA용 인증서라는 정보를 붙여준다. 어디선가 반드시 추가하란다.
- 나머지는 다 파일이름을 넣어주는 것이다.


이제 나온 `cert.cer` 파일을 윈도우에 박아줘야 한다. 이 인증서를 더블클릭해서 열고 '인증서 설치' > 저장소 위치를
'로컬 컴퓨터'로 > '모든 인증서를 다음 저장소에 저장'에서 '찾아보기'의 '신뢰할 수 있는 루트 인증 기관(Trusted Root
Certification Authority)'를 선택하고 설치하면 된다.


이제 **UEFI 플랫폼 키 인증서**와 **커널 모드 드라이버 인증서**를 만들어보자.


### UEFI 플랫폼 키 인증서 인증서 만들기
상위 폴더에서 platform-key 폴더를 만들고 아래 코드를 실행한다.

``` powershell
cd ../platform-key

# 개인키 생성
openssl genrsa -aes256 -out private.key 2048
```

그 다음, 또 다시 `cert-request.conf`를 만들고 복붙하자.

```
[ req ]
default_bits = 2048
default_md = sha256
default_keyfile = private.key
distinguished_name = localhost_uefi_platform_key
extensions = v3_user

[ v3_ca ]
basicConstraints = CA:FALSE
authorityKeyIdentifier = keyid, issuer
subjectKeyIdentifier = hash
keyUsage = digitalSignature
nsCertType = sslCA, emailCA, objCA

[ localhost_uefi_platform_key ]
countryName_default = 

# 기관
organizationName_default = Localhost

# 기관 부서
organizationalUnitName_default  = 

# 이 인증서의 이름
commonName_default = Localhost UEFI Platform Key Certificate
```

**여기부터는 만드는 중**


`certlm.msc`를 닫고 나서 다시 실행하여 `개인용\인증서` 또는 `Personal\Certificates`에 새로 생긴
`Localhost UEFI Platform Key Certificate`라는 이름의 인증서를 확인한다.


### 커널 모드 드라이버 인증서 만들기
아래 코드를 복붙한다.

``` powershell
$cert_params = @{
    Type = 'CodeSigningCert'
    Subject = 'CN=Localhost Kernel Mode Driver Certificate'
    FriendlyName = 'Localhost Kernel Mode Driver Certificate'
    TextExtension = '2.5.29.19={text}CA=0'
    Signer = $root_cert
    HashAlgorithm = 'sha256'
    KeyLength = 2048
    KeyAlgorithm = 'RSA'
    KeyUsage = 'DigitalSignature'
    KeyExportPolicy = 'Exportable'
    NotAfter = (Get-Date).AddYears(10)
    CertStoreLocation = 'Cert:\LocalMachine\My'
}

$km_cert = New-SelfSignedCertificate @cert_params
```

`certlm.msc`를 닫고 나서 다시 실행하여 `개인용\인증서` 또는 `Personal\Certificates`에 새로 생긴
`Localhost Kernel Mode Driver Certificate`라는 이름의 인증서를 확인한다.



### 인증서 만들기 마무리
이제 만든 세 인증서를 내보낸다. 내보내는 방법은 `certlm.msc`에서 `개인용\인증서`에 가서 각 인증서를
더블클릭한 후 자세히 > 파일에 복사를 누른다. 인증서 내보내기 마법사에서 아래 옵션을 선택한다.

- `예, 개인 키를 내보냅니다.` 선택
- 기본값 (개인정보 교환 - PKCS #12, 가능한 경우 인증 경로에 있는 인증서 모두 포함, 인증서 개인 정보 사용)
- '암호' 선택: 암호를 입력하고 '암호화' 칸에서 `AES256-SHA256` 선택
- 내보낼 경로 선택, 파일 이름은 저기 아래를 참고

이 방법으로 `.pfx` 확장자의 개인용 키를 내보냈을 것이다. 그 다음 같은 인증서로 위 과정을 다시 반복하되,
아래 옵션을 선택한다.

- `아니오, 개인 키를 내보내지 않습니다.` 선택
- 기본값 (`DER로 인코딩된 바이너리 X.509` 선택)

이제 `.cer` 확장자의 파일도 생겼을 것이다.  
이 과정을 세 인증서에 대해 반복하되, 파일의 이름은 아래와 같이 한다.
```
// Root CA 인증서
localhost-root-ca.cer
localhost-root-ca.pfx

// 커널 모드 드라이버 인증서
localhost-km.cer
localhost-km.pfx

// UEFI 플랫폼 키 인증서
localhost-pk.cer
localhost-pk.pfx
```


## UEFI 펌웨어의 플랫폼 키 설정
~~... 설정하고 올게요 빠이염~~
... UEFI가 PK 인증서를 뱉어요.. 않이...
제가 못했는데 튜토리얼을 짤 수는 없는데.. ㅋㅋㅋㅋㅋㅋ
조졌다
