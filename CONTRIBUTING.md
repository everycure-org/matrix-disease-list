<!-- omit in toc -->
# Contributing to MATRIX disease list

First off, thanks for taking the time to contribute! ❤️

All types of contributions are encouraged and valued. See the [Table of Contents](#table-of-contents) for different ways to help and details about how this project handles them. Please make sure to read the relevant section before making your contribution. It will make it a lot easier for us maintainers and smooth out the experience for all involved. The community looks forward to your contributions.

<!-- omit in toc -->
## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [I Have a Question](#i-have-a-question)
- [I Want To Contribute](#i-want-to-contribute)
  - [Reporting Bugs](#reporting-bugs)
  - [Suggesting Enhancements](#suggesting-enhancements)
  - [Your First Code Contribution](#your-first-code-contribution)
  - [Improving The Documentation](#improving-the-documentation)
- [Styleguides](#styleguides)
  - [Commit Messages](#commit-messages)
- [Join The Project Team](#join-the-project-team)


## Code of Conduct

This project and everyone participating in it is governed by the
[MATRIX disease list Code of Conduct](https://github.com/monarch-initiative/matrix-disease-list/blob/master/CODE_OF_CONDUCT.md).
By participating, you are expected to uphold this code. Please report unacceptable behavior
to <info@monarchinitiative.org>.


## I Have a Question

> If you want to ask a question, we assume that you have read the available [Documentation](https://monarch-initiative.github.io/matrix-disease-list/).

Before you ask a question, it is best to search for existing [Issues](https://github.com/monarch-initiative/matrix-disease-list/issues) that might help you. In case you have found a suitable issue and still need clarification, you can write your question in this issue. It is also advisable to search the internet for answers first.

If you then still feel the need to ask a question and need clarification, we recommend the following:

- Open an [Issue](https://github.com/monarch-initiative/matrix-disease-list/issues/new).
- Provide as much context as you can about what you're running into.

We will then take care of the issue as soon as possible.

## I Want To Contribute

> ### Legal Notice <!-- omit in toc -->
> When contributing to this project, you must agree that you have authored 100% of the content, that you have the necessary rights to the content and that the content you contribute may be provided under the project license.

### Reporting Bugs

<!-- omit in toc -->
#### Before Submitting a Bug Report

A good bug report shouldn't leave others needing to chase you up for more information. Therefore, we ask you to investigate carefully, collect information and describe the issue in detail in your report. Please complete the following steps in advance to help us fix any potential bug as fast as possible.

- Make sure that you are looking at the latest versio of the MATRIX disease list.
- To see if other users have experienced (and potentially already solved) the same issue you are having, check if there is not already a bug report existing for your bug or error in the [bug tracker](https://github.com/monarch-initiative/matrix-disease-list/issues?q=label%3Abug).

<!-- omit in toc -->
#### How Do I Submit a Good Bug Report?

We use GitHub issues to track bugs and errors. If you run into an issue with the project:

- Open an [Issue](https://github.com/monarch-initiative/matrix-disease-list/issues/new). (Since we can't be sure at this point whether it is a bug or not, we ask you not to talk about a bug yet and not to label the issue.)
- Explain the issue you observe with the list or its surrounding infrastructure, and what would expect instead.
- Please provide as much context as possible and describe the *reproduction steps* that someone else can follow to recreate (or re-observe) the issue on their own.
- Provide the information you collected in the previous section.

Once it's filed:

- The project team will label the issue accordingly.
- A team member will confirm your observation. If there are is no obvious way to confirm the issue, the team will ask you for those steps and mark the issue as `needs-information`. Bugs with the `needs-information` tag will not be addressed until they can be reliably confirmed.
- If the team is able to confirm the issue, it will be marked `needs-fix`, as well as possibly other tags (such as `critical`), and the issue will be left to be [implemented by someone](#your-first-code-contribution).


### Suggesting Enhancements

This section guides you through submitting an enhancement suggestion for MATRIX disease list, **including completely new features and minor improvements to the existing list**. Following these guidelines will help maintainers and the community to understand your suggestion and find related suggestions.

<!-- omit in toc -->
#### Before Submitting an Enhancement

- Make sure that you are looking at the latest version of the disease list.
- Read the [documentation](https://monarch-initiative.github.io/matrix-disease-list/) carefully and find out if the enhancement you are looking for is already covered.
- Perform a [search](https://github.com/monarch-initiative/matrix-disease-list/issues) to see if the enhancement has already been suggested. If it has, add a comment to the existing issue instead of opening a new one.
- Find out whether your idea fits with the scope and aims of the project. It's up to you to make a strong case to convince the project's developers of the merits of this enhancement. Keep in mind that we want features that will be useful to the majority of our users and not just a small subset.

<!-- omit in toc -->
#### How Do I Submit a Good Enhancement Suggestion?

Enhancement suggestions are tracked as [GitHub issues](https://github.com/monarch-initiative/matrix-disease-list/issues).

- Use a **clear and descriptive title** for the issue to identify the suggestion.
- Provide a **step-by-step description of the suggested enhancement** in as many details as possible.
- **Describe the current state** and **explain what you would like to see instead** and why. At this point you can also tell which alternatives do not work for you.
- **Explain why this enhancement would be useful** to most MATRIX disease list users. You may also want to point out the other projects that solved it better and which could serve as inspiration.

<!-- You might want to create an issue template for enhancement suggestions that can be used as a guide and that defines the structure of the information to be included. If you do so, reference it here in the description. -->

### Your First Code Contribution

- If you would like to contribute the fix yourself, please indicate this on the the issue you submitted and we will help you find your way around.

### Improving The Documentation

The documentation can be edited by clicking the pencil button in the top right corner of each page.

## Styleguides
### Commit Messages

In the spirit of Open Science collaboration, we value positive and adequate commit messages (see [this guide](https://incenp.org/dvlpt/docs/vcs-good-practices/index.html)).

## Join The Project Team

If you like to join the team, please open an issue on the [GitHub issue tracker](https://github.com/monarch-initiative/matrix-disease-list/issues) explaining how you want to be involved.

## Developer instructions

### Re-creating the disease list

The disease list is build using:

```
sh build-list.sh
```

Some notes for developers to understand the process:

- `build-list.sh` wraps a simple `make` call which is itselves wrapped by a docker container (the [Ontology Development Kit (ODK)](https://github.com/INCATools/ontology-development-kit)).
- `odk.sh` is a simple wrapper script we use in the OBO ontology community to access the ODK, which is essentially a huge docker container with all tools installed we need for executing ontology related workflows.
- `Makefile` is a regular gnu-make container for all the targets related to the disease list. Basically a super simple data workflow language. For example, the `matrix-disease-list.tsv` build target in the `Makefile` contains the command needed to created the disease list.

### Updating / adding filters

- All filter criteria (not the filtering itself!) are implemented in [this SPARQL query](sparql/matrix-disease-list-filters.sparql).
- The filter process works as follows:
  - Define a filter criterion in [this SPARQL query](sparql/matrix-disease-list-filters.sparql) (look for the `FILTER` section of the query). The pipeline will produce a TSV file which contains all the filter criteria defined in this query.
  - Implement the filter conditions in [this Python script](scripts/matrix-disease-list.py). The pipeline will seperate "diagnosable" from other kinds of disease concepts using filter rules.

### PR reviews and merging

- The person that creates the PR should assign themselves
- Only the assigned person is allowed to merge a PR - not the reviewers
- Every PR that alters the disease list should be reviewed by at least 3 people

<!-- omit in toc -->
## Attribution
This guide is based on the **contributing-gen**. [Make your own](https://github.com/bttger/contributing-gen)!
