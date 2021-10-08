---
layout: case-study
permalink: /vl-csr/
title: "Annotation Instruction"
author_profile: false
---

{% include base_path %}

## Task Definition

* **INPUT**
  * `premise` a clip of 4 seconds long from the video
  * `hypothese` a sentence describing a subsequent event
  * `question` a question asking about the event happening in between (_abductive_) or afterwards (_predictive_)

* **OUTPUT**
  * `answer` answer(s) to the question

* **Auxiliary INFO**
  * `thumbnail` the thumbnail/cover of the video
  * `clip-bg` title and desc of the clip
  * `movie-bg` title and background of the movie

## Annotation

* **Feasibility**

  **1-1.** Whether there is _ghost entity_ or _typo_ in `answer` that cannot be detected or interpreted from `premise` or `hypothese`?    
      A. *yes*;   B. *yes, but can be predicted by inference*;  C. *no*

  **1-2.** If you choose A for 1-1, then whether the _ghost entity_ or _typo_ can be predicted or interpreted based on `thumbnail`, `clip-bg`, or `movie-bg`?    
      A. *yes for* `thumbnail`;   B. *yes for* `clip-bg`;   C. *yes for* `clip-bg`+`movie-bg`;    D. *yes for* `thumbnail`+`clip-bg`+`movie-bg`;    E. *no*

  **1-3.** If you choose C for 1-1 or A/B/C/D for 1-2, then whether there is detail leakage from textual information that makes it too easy to get the answer? (*e.g. just change 1 or 2 words of the source sentence*)   
      A. *yes*;   B. *no*

* **Multimodality**

  **2-1.** If you choose B/C for 1-1 or A/B/C/D for 1-2, then whether the answer can be generated based on information from only one modality (*e.g. visual or textual*)?   
      A. *yes, based on visual info*;   B. *yes, based on textual info*;  C. *no, we need both*
  
  **2-2.** If you choose A/C for 2-1, then what kind(s) of visual information is required to be distilled for answering? (multi-choice)   
      A. *object-attribute*;  B. *scene/place signals*;   C. *human-emotion*;   D. *motion/action*;   E. *spatio-temporal relation*;  F. *others*
  
  **2-3.** If you choose C for 2-1, then how can one associate information from the two modalities together? (multi-choice)   
      A. *basic grounding/alignment*;   B. *the two modalities can help specify the events described by each other*;  C. *daily commonsense reasoning*;   D. *others*

* **CommonSense Reasoning**

  **3-1.** If you choose B/C for 1-1 or A/B/C/D for 1-2, then whether commonsense knowledge is required to get the answer? If so, what kind(s) of commonsense knowledge is included? (multi-choice)   
      A. *no*;  B. *object-attribute*;  C. *basic actions/motions of people/objects*;   D. *correlation between events*;  E. *change in people's mental states*;  F. *social interactions among people & objects*;  G. *others*
  
  **3-2.** Please write down the `rationale` of how to get the `answer` to the `question`. If you think the provided information is insufficient, then explain why the `question` is unanswerable.    


---

## Examples

{% for post in site.example reversed %}
  {% include case-study-single.html %}
{% endfor %}
