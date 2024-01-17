# Getting Started
[LCKChat](https://github.com/yeseong9769/lckchat_app) 애플리케이션에 적용되는 챗봇입니다. LCK 정보에 대한 다양한 질문에 대한 답변을 제공합니다.

## Prerequisites
You need to have python and [rasa](https://rasa.com/docs/rasa/installation/environment-set-up) installed on your system to run it. 

## How to run
Chatbot과 대화를 하기 위해서는 다음과 같은 명령어를 입력해야 합니다. 아래의 명령어를 입력하면 모델이 로드되고, 챗봇과 대화를 할 수 있습니다.
```bash
rasa test
```

## Built With 
* [Python](https://www.python.org/) - The HTTP API was built in python
* [RASA Core](https://rasa.com/docs/core/) - The Dialogue Management was done with it
* [RASA NLU](https://rasa.com/docs/nlu/) - The Natural Language processing was done with it
* [SpacyNLP](https://spacy.io/) - The NLP model was built with it (ko_core_news_lg)

## Configuration for Rasa NLU
```bash
# https://rasa.com/docs/rasa/nlu/components/
language: ko

pipeline:
  - name: SpacyNLP
    model: "ko_core_news_lg"
  - name: SpacyTokenizer
  - name: SpacyFeaturizer
  - name: RegexFeaturizer
  - name: LexicalSyntacticFeaturizer
  - name: CountVectorsFeaturizer
  - name: CountVectorsFeaturizer
    analyzer: word
  - name: DIETClassifier
    epochs: 200
  - name: CRFEntityExtractor  # 추가
  - name: EntitySynonymMapper
  - name: ResponseSelector
    epochs: 100
  - name: FallbackClassifier
    threshold: 0.2
```

## Configuration for Rasa Core
```bash
# https://rasa.com/docs/rasa/core/policies/
policies:
  - name: MemoizationPolicy
  - name: RulePolicy
  - name: UnexpecTEDIntentPolicy
    max_history: 5
    epochs: 100
  - name: TEDPolicy
    max_history: 5
    epochs: 100
    constrain_similarities: true
```