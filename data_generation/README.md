# Data Generation 

## 📂 version2
이미 존재하는 템플릿 이미지를 토대로 bbox 위치와 크기 등을 결정한 뒤에, 명함 이미지 생성 (가로 명함)
> **구현 과정**
1) 템플릿 이미지를 구한다 (ex. 미리캔버스) 
2) 해당 템플릿 이미지에 대해 annotation (이때, coco-annotator라는 annotation tool 사용)을 진행하여 bbox 위치와 크기 등을 json 파일로 추출한다. 
3) 만들어진 json 파일의 정보를 토대로, 텍스트 내용을 랜덤하게 변경하여 명함 이미지 데이터를 생성한다.

## 📂 version3
회사 이름/이름/직책&부서/숫자 정보 등에 대해 템플릿 클래스를 만든 후, 이를 랜덤하게 조합하여 명함 이미지 생성 (가로 명함)
> **구현 과정**
1) 각 카테고리에 대해 x축 상의 위치가 왼쪽/가운데/오른쪽 랜덤으로 지정된다.
2) 각 카테고리 항목의 포함 여부는 랜덤하게 결정된다. (단, 확률은 카테고리마다 상이)

## 📂 version4
회사 이름/이름/직책&부서/숫자 정보 등에 대해 템플릿 클래스를 만든 후, 이를 랜덤하게 조합하여 명함 이미지 생성 (세로 명함)
> **구현 과정**
1) 각 카테고리에 대해 x축 상의 위치가 왼쪽/가운데/오른쪽 랜덤으로 지정되며, 명함 이미지의 너비를 기준으로 랜덤하게 조정된다. 
   각 카테고리에 대해 y축 상의 위치가 명함 이미지의 높이를 기준으로 랜덤하게 조정된다. 
2) 각 카테고리 항목의 포함 여부는 랜덤하게 결정된다. (단, 확률은 카테고리마다 상이)
3) 각 카테고리 항목의 정렬 순서는 템플릿에 따라 결정된다.

## 📂 unused
명함 데이터 생성을 위해 시도한 코드 