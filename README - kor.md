# Namoutils/ex6 - Namodular

Namodular is a python script that started as a sublime text 3 plugin. It's main purpose is to help the code reflect project folder structures  



모듈러한 코딩을 할 때에는 폴더 구조의 변경이 매우 잦습니다. 그런데 폴더의 구조가 변할 때 그 변화가 코드에 반영되지 않으면 오류가 발생할 것입니다. 





python 

namodular는 기본적으로 sublime text 3 와 함께 사용할 수 있는 플러그인으로 만들어져 있습니다. 그러나 서브라임 텍스트는 인터페이스 적인 측면에서의 편의를 제공할 뿐 구현 자체가 sublime API에 의존하지는 않기 때문에 독립적인 python 스크립트로 사용가능합니다. namodular의   


리소스 로딩에 효과적입니다. 



사용법 


	




구현 

namodular는 그 구현이 단순하지만은 않습니다. namodular와 똑같은 기능을 구현하기 위한 가장 단순한 방법은 namodular가 적용된 디렉토리 혹은 git repo 내의 모든 파일을 매 업데이트 시마다 다 돌면서 체크하는 것입니다. 하지만 이는 성능적인 낭비가 매우 심하기 때문에 namodular는 좀더 효율적인 방식을 고안해내었습니다. 

나모듈라 스크립트는 현재는 직접적으로 실행해줘야 코드가 폴더구조를 반영하게 됩니다. 항상 모든 커맨드 블록들이 프로젝트디렉토리를 제대로 반영한 상태를 보장하기 위해선 파일이 수정될 때마다 실행해주면 됩니다. 

기본적으로 나모듈라는 스크립트의 실행은 3가지 단계로 이루어집니다. 

1. update folder structure 

2. link output files 

	
	- virtual branch 
	
3. write to output files    





## Updates

### 190212
- low reusablity issue of forin cmd lines and printable formats 
	- need to make root based path manipulation easier 
- forin command blocks with r tag should be updated when any of offsprings are changed 
	- set **-r** tag as default, updated when any of the offspring structure changes
	
### 190225
- support for other line comment syntax added, default as lua comment syntax. Should use other language, user should configure what string starts a line comment in config file under _namodular directory
