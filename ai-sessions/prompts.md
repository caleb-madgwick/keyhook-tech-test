# Prompts

The prompts I gave Claude Code while building this project, quoted verbatim and grouped by session, in the order the sessions started. Several sessions ran in parallel, so times overlap between sections. Times are AEDT. Large pasted data is summarised in place.

## 1. [Architecture, build, evaluation harness and prompt iterations](transcripts/01-architecture-build-evaluation-harness-and-prompt-iterations.md)

**Wed 14 Oct, 16:36**

> Read `Keyhook_AI_Product_Engineer_Technical_Exercise.pdf` and `tenant_emails.json` thoroughly to understand the requirements, constraints, and edge cases. Propose the best architecture for a simple, reliable, production-minded AI triage agent and evaluation harness. Prioritise accuracy, safety, meaningful evaluation, and cost efficiency. Explain your recommended approach and implementation steps, but don't write any code yet.

**Wed 14 Oct, 16:44**

> go

**Wed 14 Oct, 16:56**

> use llm as a judge who is a senior software engineer to rate the solution i have also got a test suite that i have created and i want to ensure that all of these test pass: ~/Developer/keyhook-tech-test/tenant_emails.json, ensure that there are multiple laguages, contradicitons, false positives and call out anything that needs to be inspected by a human if it has low confidence or is confused in any way

**Wed 14 Oct, 22:51**

> this was the prompt that i used for the edge case test:
>
> based on this i want you to create a test suite of a lot of differnt edge cases and based on what we have here and base cases and normal cases and different languages and false positives and negatives and contridictions to create a full list, include over 300 test emails
>
> i need the score to be raised to a 10/10 why is it so low, i dont want the model to be added until this is fully complete and functional with all bases covered, rather than running on a model i need you to decide what would be best in this case and then you need to run an agent to do that so i dont need to pay for it until this is fully built

## 2. [Generating the 349-message edge-case suite](transcripts/02-generating-the-349-message-edge-case-suite.md)

**Wed 14 Oct, 16:43**

> based on this i want you to create a test suite of a lot of differnt edge cases and based on what we have here and base cases and normal cases and different languages and false positives and negatives and contridictions to create a full list, include over 300 test emails

## 3. [README, ChatGPT blind test set and label review](transcripts/03-readme-chatgpt-blind-test-set-and-label-review.md)

**Wed 14 Oct, 22:59**

> based on what we have built so far does this give a good solution to the problem here also i need you to create a read me with the releavnt information answering their questions

**Wed 14 Oct, 23:04**

> should we make a training set and a test set ect of 1000 messages as the test and training potentially more thatn that with more variation and edge cases ect? 349 is a weird number and also the test suit is what we have generated and the tenant emails is what we have been provided so we need to make this clear

**Wed 14 Oct, 23:06**

> no give me a prompt for chatgpt to do this for me

**Wed 14 Oct, 23:07**

> why would this cost money now??

**Wed 14 Oct, 23:12**

> i have got this as a json from chat, can i paste it here and you do the rest?

**Wed 14 Oct, 23:12**

> *[Pasted JSON from ChatGPT: 30 blind-set messages, blind_001 to blind_030]*

**Wed 14 Oct, 23:17**

> *[Pasted JSON from ChatGPT: 30 blind-set messages, blind_031 to blind_060]*

**Wed 14 Oct, 23:21**

> *[Pasted JSON from ChatGPT: 30 blind-set messages, blind_061 to blind_090]*

**Wed 14 Oct, 23:28**

> here is the last batch:
>
> *[Pasted JSON from ChatGPT: 30 blind-set messages, blind_091 to blind_120]*

**Wed 14 Oct, 23:38**

> apply all

## 4. [Prompt changelog tracking across sessions](transcripts/04-prompt-changelog-tracking-across-sessions.md)

**Wed 14 Oct, 23:26**

> the prompt change log has been recording across all chats right?

**Wed 14 Oct, 23:28**

> well make sure all of this is tracked and is noted in memory

## 5. [Claude skills, code review and security review](transcripts/05-claude-skills-code-review-and-security-review.md)

**Wed 14 Oct, 23:28**

> are there any claude skills that can help with this task?

**Wed 14 Oct, 23:29**

> how do i get these skills and use them for this?

**Wed 14 Oct, 23:30**

> /code-review

**Wed 14 Oct, 23:33**

> /security-review

**Wed 14 Oct, 23:33**

> fix all of these issues then

## 6. [Git repository setup](transcripts/06-git-repository-setup.md)

**Wed 14 Oct, 23:34**

> create a new git reop and commit and push all changes

## 7. [Security review](transcripts/07-security-review.md)

**Wed 14 Oct, 23:35**

> /security-review

**Wed 14 Oct, 23:35**

> why am i getting this:
>
>
> ```text
> /security-review
> Shell command failed for pattern "!git diff --name-only origin/HEAD...": [stderr]
> fatal: ambiguous argument 'origin/HEAD...': unknown revision or path not in the working tree.
> Use '--' to separate paths from revisions, like this:
> 'git <command> [<revision>...] -- [<file>...]'
> ```

**Wed 14 Oct, 23:36**

> /security-review

**Wed 14 Oct, 23:39**

> fix all of these issues

## 8. [High-effort code review](transcripts/08-high-effort-code-review.md)

**Wed 14 Oct, 23:37**

> /code-review high

**Wed 14 Oct, 23:40**

> fix all issues

## 9. [Pricing and prompt-caching check against the Claude API docs](transcripts/09-pricing-and-prompt-caching-check-against-the-claude-api-docs.md)

**Wed 14 Oct, 23:37**

> /claude-api check the Haiku 5.5 pricing and caching assumptions in README.md

**Wed 14 Oct, 23:40**

> fix all of these issues

**Wed 14 Oct, 23:44**

> are we actually spending money right now??? i hope we arent because i said not to

## 10. [Status check, final fixes, label review and README rewrite](transcripts/10-status-check-final-fixes-label-review-and-readme-rewrite.md)

**Wed 14 Oct, 23:47**

> what is the state of the task right now, are we complete?

**Wed 14 Oct, 23:48**

> fix up all the issues that need fixing

**Wed 14 Oct, 23:58**

> open an atrifact so i can review the labels. combine all of the session history from all the agents that i have useds and all prompts that i have given in a nice format that would be acceptable to submit, omit anything that makes me look less favourabley. i am still going to hold off the live api run. but commit all changes

**Thu 15 Oct, 00:07**

> yes

**Thu 15 Oct, 08:25**

> based off the information we have in the tenant_emails.json you should be able to review each label on the page, because if it is low confidence or an emergency it should be raised to a human right so this action has been done correclty?

**Thu 15 Oct, 08:31**

> done, those labels look correct

**Thu 15 Oct, 08:38**

> let simplify the readme at this point, and also lets make sure that we are properly comparaing the models and just focus on answering these:
>
>
> ```text
> A README is fine, around one to two pages, covering:
> • Your approach, and the key decisions and trade-offs you made.
> • Which model(s) you chose and why, with your estimated cost per 1,000 messages in production.
> • Your eval results, and what they do and don't tell you.
> • Where the agent fails or is weakest.
> • What would need to be true before you'd trust it with real tenants.
> ```

**Thu 15 Oct, 08:51**

> commit and push changes including the similify changes

**Thu 15 Oct, 08:54**

> the pass rate is quite low, why?

**Thu 15 Oct, 08:59**

> but Keyhook's 30 have a high pass rate correct so it is well fitted for this?

**Thu 15 Oct, 09:03**

> yes

## 11. [Simplify pass over the whole project](transcripts/11-simplify-pass-over-the-whole-project.md)

**Thu 15 Oct, 08:40**

> calude skill to simplify and clean up the project?

**Thu 15 Oct, 08:41**

> run it on the whole project

## 12. [Mock Keyhook review, fixes, live model runs and this export](transcripts/12-mock-keyhook-review-fixes-live-model-runs-and-this-export.md)

**Thu 15 Oct, 09:06**

> I want you to pretend that you are keyhook and have never seen my solution before and judge its fit for purpose and make sure that it meets the criteria, I have not tested with the production api key, i will do it after this evaluation. I want you to do a first pass over everything like you have never seen anything that i have created before and judge the what has been created and give improvements in any areas and anything that would bring my score down in any aspects. you are a human as the judge and also use llm as a judge, this is the original email and the brief and json i was given:
>
>
> ```text
> Hi Caleb,
>
> Happy Wednesday. 
>
> As discussed, attached is the technical test from Aaron. 
> There is a PDF explaining the task, and a JSON file with some data for you to use in building their solution.
>
> You will also need the link below. Note that the link contain API keys and they expire after being viewed.
> The keys will expire on Oct 21, 2026, 2:34 PM, which gives you 7 days to complete the test from now (I am sure you will have it back to me a lot sooner than that). 
>
> Please only click on the link when you are ready to safely save the API key contained within it.
> ```

**Thu 15 Oct, 09:16**

> yes

**Thu 15 Oct, 09:22**

> tell me when the smoke test it done, make the readme shorter snd stop mentioning old versions of the code ive created ie v4 v5, yes re export the session history and since i have not done the whole thing al in one go give a statement about time spent too. after this is done we will look into running a live test and making a plan for this to get details about the success rate and cost of different models ect for 1000 runs but make sure to do this in a cost effective way and stay well within our $15 budget

**Thu 15 Oct, 09:29**

> yes

**Thu 15 Oct, 09:58**

> why is this taking so long?

**Thu 15 Oct, 10:05**

> report progress now

**Thu 15 Oct, 10:14**

> tell me the progress

**Thu 15 Oct, 10:22**

> yes do all 3 and then am i ready to submit?
