---
layout: case-study
permalink: /hyp-vlr/
title: "Hypothetical Visual-Linguistic Reasoning"
author_profile: false
---

{% include base_path %}
{% include toc %}

Train
---
{% for post in site.exampletrain reversed %}
  {% include case-study-single.html %}
{% endfor %}


Validation
---
{% for post in site.examplevalid reversed %}
  {% include case-study-single.html %}
{% endfor %}
