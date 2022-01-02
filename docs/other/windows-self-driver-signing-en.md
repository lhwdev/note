---
title: Self-signing on Windows
date: 2021-11-16
---


# Self-signing on Windows

This document assumes that those reading this document has basic expertises for shell and programming.
If you are not, you may try these, but it will be... painstaking.  
Translated from [original Korean document](https://lhwdev.github.io/note/other/windows-self-driver-signing)
I had written.
I changed my Windows locale to write this..

!!! warning "**Alert**"
    Get yourself informed enough.
    I do not guarantee if this would work.

!!! danger "🚧 **Under construction**"
    Going under translating
    [original Korean document](windows-self-driver-signing).

## Why?

I found Synchronous Audio Router(SAR) which can,

- add virtual audio device (UNLIMITED; as far as your Windows stands)
- FOSS
- just liked it
- high performance, low latency

So I made up mind to install it. However...

> ## Unsigned prereleased drivers note
> Prereleases of SAR are unsigned. That means that it is required to enable testsigning boot option
  to make Windows load the driver. Else the driver won't be loaded.

At this point I'd turned Secure Boot and gotta upgrade to Windows 11.
I also considered security, so turning on `testsigning` was not eligible.

At that time I came across [one issue](https://github.com/eiz/SynchronousAudioRouter/issues/86) saying:
> UPDATE 3: SUCCESS!!!!!!!!! I am running the latest SAR in Reaper as we speak on windows 10 without testmode.

(lhwdev was determined!)


## Get started

- Before you start, find ways to set **UEFI Platform Key** on your device. If your UEFI does
  not support this, you cannot do these all.
- This document covers a lot of dangerous things like 'setting UEFI Platform Key, editing EFI
  boot partition, modifying Windows system registry'. Recommend backup in advance. ~~(but the
  writer did not)~~

!!! info "**Reference**"
    If you want, take a look at that issue I began from, and
    [the issue referenced from there](https://github.com/valinet/ssde).

## Creating Certificates & Configuration
I used builtin powershell command `#!powershell New-SelfSignedCertificate` to create certificates
first, but I came to use OpenSSL. If you want, you can follow
[this one](https://github.com/HyperSine/Windows10-CustomKernelSigners/blob/master/asset/build-your-own-pki.md).

We are going to create certificates which is only valid on your device. (Virtual) Root Certificate
Authority, (Root CA) and create other certs using it.
I heard these methods work on Windows 11.

Launch Powershell with **admistrative privilege**. (not needed to create certs; needed after that)
This article is based on Powershell.

The resulting files are like this:
``` markdown
root-ca
- private.key
- cert-request.conf
- cert-request.csr
- cert.cer
- serial.srl
platform-key
- private.key
- cert-request.conf
- cert-request.csr
- cert.cer
- PK.unsigned.esl
- PK.esl
- PK.old.esl
kernel-mode
- private.key
- cert-request.conf
- cert-request.csr
- cert.cer
```

### Installing OpenSSL
OpenSSL is bundled when installing Git, so to use it check out
[this StackOverflow answer](https://stackoverflow.com/a/51757939/10744716).

Those with Chocolatey installed can use `#!powershell choco install openssl` in privileged shell.
Use `#!powershell refreshenv` to use new installed one without restarting shell. (bundled with choco)


### Creating Root CA Certificate

If the certificate of Root CA itself is trusted, certs that CA created will be trusted.

Create `root-ca` directory, and run the following.
``` powershell
cd root-ca

# Generate private key
openssl genrsa -aes256 -out private.key 2048
```
Demonstration of this is:

- `-aes256`: Encrypt the created private key. If you want to omit this you can, but it would be bad for
  security?
- `-out private.key`: Into the file 'private.key'.
- `2048`: The length of key.

Then copy-paste below and save to `cert-request.conf`, modifying what you want.
Do not modify things like countryName, (it does nothing) instead edit countryName_default,
for instance.

``` properties
[ req ]
default_bits = 2048
default_md = sha256
default_keyfile = private.key
distinguished_name = localhost_root_ca
extensions = v3_ca
req_extensions = v3_ca

[ v3_ca ]
basicConstraints = critical, CA:TRUE # , pathlen:0 # This option can adjust maximum number of 'intermediate CA'.
subjectKeyIdentifier = hash
keyUsage = keyCertSign, cRLSign

[ localhost_root_ca ]
countryName = Country Name (2 letter code)
countryName_default = 

organizationName = Organization Name (eg, company)
organizationName_default = Localhost # or what you want?

organizationalUnitName = Organizational Unit Name (eg, section)
organizationalUnitName_default  = 

commonName = "Common Name (eg, your name or your server's hostname)"
commonName_default = Localhost Root Certification Authority # or the name you want??
```

Return to shell, execute below to create Certificate Signing Request(CSR).

``` powershell
openssl req -new -key private.key -out cert-request.csr -config cert-request.conf
```

You will see below.
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
Enter the password (if you set), press enter repeatedly as we set default values in `cert-request.conf`.

Now you can see `cert-request.csr`. Create actual cert with command below.
```powershell
openssl x509 -req -days 18250 -extensions v3_ca `
  -in cert-request.csr -signkey private.key `
  -out cert.cer -extfile cert-request.conf
```

- Replace 18250 in `-days 18250` with the duration you want the cert to be valid. Note that 18250 equals to
  approximately 50 years. (or 365 * 50)
- `-extensions v3_ca` loads `[ v3_ca ]` part from .conf file you'd written.
- The left are file names.


Now you need to register `cert.cer` to Windows so that it is trusted.
Double click the cert created from above, `cert.cer`, and 'Install certificate...' >
'Local Machine' > 'Place all certificates in the following store', 'Browse... >
'Trusted Root Certification Authorities'. Now if you open your cert, it will be shown
as valid.


Now let's create **UEFI Platform Key Certificate** and **Kernel Mode Driver Certificate**.


### Creating UEFI Platform Key(PK) Certificate
Move to the root directory we started, new folder 'platform-key', and run below.

``` powershell
cd ../platform-key

# Generate personal key
openssl genrsa -aes256 -out private.key 2048
```

After, new file `cert-request.conf` and copy-paste, once more.

``` properties
[ req ]
default_bits = 2048
default_md = sha256
default_keyfile = private.key
distinguished_name = localhost_uefi_platform_key
extensions = v3_req

[ v3_req ]
basicConstraints = CA:FALSE
authorityKeyIdentifier = keyid, issuer
subjectKeyIdentifier = hash
keyUsage = digitalSignature

[ localhost_uefi_platform_key ]
countryName = Country Name (2 letter code)
countryName_default = 

organizationName = Organization Name (eg, company)
organizationName_default = Localhost

organizationalUnitName = Organizational Unit Name (eg, section)
organizationalUnitName_default  = 

commonName = "Common Name (eg, your name or your server's hostname)"
commonName_default = Localhost UEFI Platform Key Certificate
```

Create CSR file.
``` powershell
openssl req -new -key private.key -out cert-request.csr -config cert-request.conf
```
Enter the password and press enterrrrrr again.

Let's make the certificate.
``` powershell
openssl x509 -req -days 18250 -extensions v3_req `
  -in cert-request.csr `
  -CA ../root-ca/cert.cer -CAcreateserial -CAserial ../root-ca/serial.srl `
  -CAkey ../root-ca/private.key `
  -extfile cert-request.conf -out cert.cer
```

- `-CA ...`: path to CA certificate (public key)
- `-CAkey ...`: same (but private key)
- `-CAcreateserial -CAserial ../root-ca/serial.srl`: Create serial file and save to serial.srl.
  This file let certificates made using CA never have serial numbers colliding.
  If serial.srl file already exists, you should exclude `-CAcreateserial` option.

Additionally you should convert private.key to .pfx file as it is used from signtool to sign
'Si Policy'.

``` powershell
openssl pkcs12 -export -out private.pfx -inkey private.key -in cert.cer
```


### Setting Platform Key of UEFI Firmware
![Set-SecureBootUefi success](ssd/set-securebootuefi.png)
*<p align="center">Cool</p>*

There are different ways depending on your device. My computer was Dell laptop, where there is
'Export Key Management', but it didn't work.  
But I got it work by using powershell command `#!powreshell Set-SecureBootUefi`.

If you want to set PK after generating all the keys you can, but you might feel sense of lose(?)
if your UEFI do not allow you to set PK.

Check your UEFI setting first and try it if exists.

In the method below using powershell, I used `efitools` through [WSL](https://docs.microsoft.com/windows/wsl/about). (but that command has some parameter like `-Hash`? I didn't try it)
In fact I couldn't find alternative for efitools, so if you find one, PR this document.

**Before trying methods below, change Secure Boot Mode in UEFI configuration.** Changing keys like
PK is blocked by default. For me, (Dell laptop) there were 'Deploy Mode' and 'Audit Mode'. Setting
it to 'Audit Mode' worked.

Get into WSL terminal.

``` bash
# Move to platform-key directory
cd $(wslpath "path to platform-key/")

# generate esl file
cert-to-efi-sig-list -g "$(cat /proc/sys/kernel/random/uuid)" cert.cer PK.unsigned.esl

# sign esl file
sign-efi-sig-list -k private.key -c cert.cer PK PK.unsigned.esl PK.esl
```
Note that .esl stands for EFI Signature List, which is a format to store signatures in UEFI firmware.

Backup esl file in advance, just in case.
``` powershell
Get-SecureBootUefi -Name PK -OutputFilePath PK.old.esl
```

Then open powershell with **administrative privilege**, (don't need to reopen if you are with) move
to platform-key directory, and enter below.

``` powershell
Set-SecureBootUEFI -Name PK -SignedFilePath PK.esl -ContentFilePath PK.unsigned.esl -Time $(Get-Date)
```

If `Set-SecureBootUEFI: Invalid certification data: 0xC0000022` shows, you may put wrong key, not
change Secure Boot Mode, or your UEFI may not support it.  
If you see something like below, congratulations. Our UEFI will trust our CA.

```
Name Bytes                Attributes
---- -----                ----------
PK   {161, 89, 192, 18…} NON VOLATILE…
```


### 커널 모드 드라이버 인증서 만들기
New directory kernel-mode-driver from root, run this.

``` powershell
cd ../kernel-mode-driver

# generate personal key
openssl genrsa -aes256 -out private.key 2048
```

Create `cert-request.conf` here again like this:

``` properties
[ req ]
default_bits = 2048
default_md = sha256
default_keyfile = private.key
distinguished_name = localhost_kernel_mode_driver
extensions = v3_req

[ v3_req ]
basicConstraints = CA:FALSE
authorityKeyIdentifier = keyid, issuer
subjectKeyIdentifier = hash
keyUsage = digitalSignature
extendedKeyUsage = codeSigning

[ localhost_kernel_mode_driver ]
countryName = Country Name (2 letter code)
countryName_default = 

organizationName = Organization Name (eg, company)
organizationName_default = Localhost

organizationalUnitName = Organizational Unit Name (eg, section)
organizationalUnitName_default  = 

commonName = "Common Name (eg, your name or your server's hostname)"
commonName_default = Localhost Kernel Mode Driver Certificate
```

Create CSR file.
``` powershell
openssl req -new -key private.key -out cert-request.csr -config cert-request.conf
```
Enter password, press enter a few times.

Create certificate.
``` powershell
openssl x509 -req -days 18250 -extensions v3_req `
  -in cert-request.csr `
  -CA ../root-ca/cert.cer -CAserial ../root-ca/serial.srl `
  -CAkey ../root-ca/private.key `
  -extfile cert-request.conf -out cert.cer
```

Again, need to convert private.key into .pfx file.

``` powershell
openssl pkcs12 -export -out private.pfx -inkey private.key -in cert.cer
```

We made all three certificates needed. (we could combine all into one, but that
would be inflexible and less secure? maybe?)


## Set Signing Policy (Si Policy)
We had to create xml file containing signing policy then convert into binary
file, but this only works in Windows Enterprise/Education Edition. So
[Download prebuild binary file.](https://www.geoffchappell.com/notes/windows/license/_download/sipolicy.zip)

이제 `selfsign.bin`을 서명해야 윈도우에서 정상적으로 인식하게 됩니다.

``` powershell
signtool sign /fd sha256 /p7co 1.3.6.1.4.1.311.79.1 /p7 . /f platform-key/private.key /p <# platform-key의 비밀번호 #> sipolicy/selfsign.bin
```

- `platform-key/private.key`: platform key의 비공개 키 경로
- `sipolicy/selfsign.bin`: 바로 위에서 다운받은 파일

이제 `selfsign.bin.p7`이라는 파일이 생겼을 것입니다. 파일의 이름을 `SiPolicy.p7b`로 바꿔주세요.
그 다음 **관리자 권한으로** 파워셸을 열고(이미 관리자 권한이면 새로 열지 않아도 됩니다.) 아래 명령어를
실행해주세요.

``` powershell
# EFI 시스템 파티션을 X: 드라이브에 마운트
mountvol x: /s

# SiPolicy 복사
cp SiPolicy.p7b X:\EFI\Microsoft\Boot\

# (안해도 상관은 없음?) EFI 볼륨 마운트해뒀던거 취소하기
mountvol x: /d
```

## Custom Kernel Signer(CKS) 켜기
CKS라는 이 값은 레지스트리의 `HKLM\SYSTEM\CurrentControlSet\Control\ProductOptions`에 저장되어
있다고 합니다. 이 값은 사실상 커널 초기화가 끝나지 않았을 때에만 설정할 수 있는데요, 자세한 원리는
[원본 문서에서 확인할 수 있습니다](https://github.com/HyperSine/Windows10-CustomKernelSigners).
저는 방법만 간단하게 설명할게요.

[우선 이 url로 들어가서 ssde.zip을 받아주세요](https://github.com/valinet/ssde/releases).
거기 안에 보면 ssde.sys가 있습니다. 이 드라이버를 서명해줄 건데요, 아래 명령어를 실행해주세요.

``` powershell
signtool sign /fd sha256 /a /ac root-ca/cert.cer /f kernel-mode-driver/private.pfx /p <비밀번호> /tr http://sha256timestamp.ws.symantec.com/sha256/timestamp ssde.sys
```

**혹시 컴퓨터를 다시 못 켤까봐 두려우신 분들은 WinPE(Windows Preinstalled Environment)를 설정하는 것을 추천드립니다.**
아래의 명령어를 실행한 후에는 윈도우 입장에서 ssde.sys가 알 수 없는 인증서로 서명되었는데,
커널 드라이버라서 실행을 못하여서 Kernel fault를 일으키게 됩니다. 즉 블루스크린이 뜨거나 복구 환경으로 들어가게
됩니다. 복구 환경으로 들어갈 수 있다면 다행이고, 아마 들어가질 겁니다. 하지만 만약 그렇지 않다면 다시 컴퓨터로
부팅할 수 없을지도 모르니까요?  
뭐 근데 아마 될거에요?


이제 드디어 적용할 시간입니다. **위에서 서명한** ssde.sys를 설치해줄 겁니다.
아래 명령어를 관리자 권한 파워셸에서 실행해주세요.
(cmd라면 `#!powershell $env:windir`을 `#!bat %windir%`로 바꾸면 됩니다.)

``` powershell
cp ssde.sys $env:windir\system32\drivers\ssde.sys
sc create ssde binpath=$env:windir\system32\drivers\ssde.sys type=kernel start=boot error=normal
```

혹시나 아래에 있는 단계를 하다가 무언가 안돼서 원래대로 되돌리려면 복구모드 명령 프롬프트에서
그냥 `C:\Windows\System32\drivers\ssde.sys`를 삭제하면 원래대로 돌아옵니다. 혹시 UEFI 설정에서 PK를
초기화했다던가 컴퓨터 설정을 바꾸다가 초기화되면 부팅이 정상적으로 안 될수도 있는데 그때 이 방법을 쓰면 돼요.

**아래 부분은 종이에 적어놓거나 휴대폰으로 보시는 걸 추천드립니다.**  
이제 컴퓨터를 재부팅하면 아마 평소와 다르게 블루스크린이 뜨거나 '시스템 복구 중' 같은 식으로 뜨다가 다른 창으로
넘어갈거에요. 이것은 부팅이 실패했고 커널 패닉이 일어났다는 뜻입니다.  

> 자동 복구에서 PC를 복구하지 못했습니다.

이제 이 부분에서 **고급 옵션**으로 들어가고, **문제 해결 > 고급 옵션 > 명령 프롬프트**를 선택합니다.
계정을 선택하고 비번을 입력하면 cmd 창이 뜰겁니다. 여기서 `#!bat regedit`을 입력하면 레지스트리 편집기가
뜹니다.
`HKEY_LOCAL_MACHINE`을 선택한 다음 `파일(F)` > `하이브 로드(L)...`을 누르고 윈도우가 설치된 경로에서
(보통 `C:/Windows`, 복구모드에선 다른 드라이브에 마운트됐을 수도 있어요) `System32 > config > SYSTEM`을 열어서
아무 이름 입력, 확인을 누릅니다. 그럼 `HKEY_LOCAL_MACHINE` 아래에 해당 '아무 이름'이라는 키가 뜰거에요.

해당 키에서 `ControlSet001` > `Control` > `CI` > `Protected`에 보면 `Licensed`라는 게 보일 거에요.
더블클릭해서 **기존의 값 0을 1로 바꾸고** 확인을 눌러줍니다.

![set-licensed](ssd/set-licensed.jpg)
이렇게요.

이제 할 일을 끝마쳤습니다. 레지스트리 편집기와 cmd 창을 닫고 다시 부팅을 하면 아마 정상적으로 될 거에요.
이제 ssde.zip을 풀은 폴더에 보면 ssde_info.exe라는 프로그램이 있는데 cmd나 파워셸에서 실행시켜 주세요.
무언가 오류가 아닌 것처럼 생긴 게 아래처럼 뜨면 성공입니다.

```
API version is 1.1
Arm count is 2
Arm watchdog status is 1
License tamper state is 0
```
이 드라이버도 우리가 만든 인증서로 서명했기 때문에, 정상적으로 실행됐다면 거의 다 끝났습니다.

이제 컴퓨터를 다시 시작해 보세요. '자동 복구에서 PC를 복구하지 못했습니다.'가 다시 뜰 가능성이 높습니다.
만약 안뜬다면 정상적으로 끝난 것이고, 만약 뜬다면 위에 설명한 것을 다시 실행하면 됩니다.

수고하셨어요. 필요하다면 UEFI에서 Secure Boot Mode를 원래대로 돌려놓아도 됩니다.
(PK를 설정하기 위해 잠시 바꿔놨었죠)


## 참고
기본적으로 참고한 문서:

- [안정적인 방법: valinet/ssde](https://github.com/valinet/ssde)
- [최초로 성공한 사례: HyperSine/Windows10-CustomKernelSigners](https://github.com/HyperSine/Windows10-CustomKernelSigners)
- [원본 PoC: Licensed Driver Signing in Windows 10](https://www.geoffchappell.com/notes/windows/license/customkernelsigners.htm)

조금 유용한 문서들:

- [미국 국방부에서 Secure Boot에 관해 쓴 글](https://media.defense.gov/2020/Sep/15/2002497594/-1/-1/0/CTR-UEFI-Secure-Boot-Customization-UOO168873-20.PDF)
