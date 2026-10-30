# Owner decisions, Sprint 20 (2026-10-30)

Recorded by Cypher from the conversation, in the owner's words where possible. **Draft: the owner corrects this file; nothing here is final until they say so.** When a decision is made, it is added here before any code or doc relies on it.

## Rules the owner gave

* **Define the names of things before using them** ("we need to define the names of things before you just plop them in there").
* **Reuse; no new words** ("I want to reuse what we have instead of inventing new syntax for everything"; "I said no new words"; "KISS"; "REUSE").
* **One way only:** "1 and only 1 consistent way to declare and reference symbolic names"; "I only want 1 way to declare and pass params to a sketch, sub or otherwise."
* **Standard YAML 1.2 only, plus tags if needed:** "we are only going to support standard yaml 1.2 references of any valid type"; "tags can be used too"; "whatever yaml 1.2 valid syntax can always be used if wanted or needed."
* **YAGNI** (walk away, `format: csv`, repeated source reads were all cut on this basis).

## Decisions

| # | Decision | Owner's words / basis |
|---|---|---|
| 1 | **Sketches are Jinja2 templates** over standard YAML 1.2. m4 rejected. | "yeah jinja2 please" |
| 2 | **Values come in with `--with name=value`** on the command line, **and `with:` when a sketch calls another**: the same word, one way. | "make the arg --with. then it matches the subsketch args right? basically we want any sketch to potentially be used as a subsketch" |
| 3 | **Names are validated:** a `--with` / `with` name the receiving file does not use is refused (nearest name offered). | "validate the input names" |
| 4 | **Composing sketches is encouraged:** one sketch may be called many times with different values. | "composing sketches is encouraged" |
| 5 | **The child is filled with values from the parent**, never the other way. | "the child get fill with values from the parent not the other way around right?" (yes) |
| 6 | **The checker runs after Jinja expansion, but a parent does not expand its children.** The child is checked on its own; the parent checks only the child's declared interface ("that's what encapsulation is for"). | "no it doesn't need the expanded children that's what encapsulation is for" |
| 7 | **The parent's names must match the child's declared output names.** | "the names need to match the declared output names" |
| 8 | **The keyword is `outputs`, not `returns`.** | "I thought we settled on outputs? ... YES! THAT WAS THE DECISION" |
| 9 | **A final state's `outcome` stays** ("walk away" is a final state in the machine, not a keyword; `on_empty: walk_away` removed). | "ok so there already is a semantic for outcome. we should keep it" ; "YAGNI" |
| 10 | **Weights are floats 0.0 to 1.0.** | "weights should be expressed as 0.0-1.0 float" |
| 11 | **Slices `a:b` exclude the stop** everywhere (inclusive "would be a disaster"). Range with `step` and option lists already exist (reuse). | "def 1. 2 would be a disaster"; "we also have step"; "and we have option list" |
| 12 | **No hidden loops.** A list passed to a source, stage or sketch is one input ("all these items are 1 thing"). | "I don't like the implicit looping ... the source should either accept a list or single item" |
| 13 | **One explicit loop, `each:`, which runs only a sketch.** | "yes that's clean" |
| 14 | **The way a loop pairs its answers with its rows goes in the `each` syntax.** (Exact form not yet decided.) | "okay put it in the each syntax" |
| 15 | **Values are passed to the child explicitly** ("we had this before and I think you removed it"). Exact form for per-row values not yet decided. | "yes we had this before" |
| 16 | **A showing is a film at a time;** the Jev reviews belong to the film, so the loop runs over films and joins to showings by `title`. | "yes I think that makes more sense" |
| 17 | **Cut:** `format: csv` file sources; reading one source several times with different params. | "yes to 1 and 2" |

| 18 | **An `each` produces a list of input/output pairs:** `[ { input: { ... }, output: { ... } }, ... ]`, one per iteration: the input row, and what the child output. No merging, no `by:`. | "1. [ {input: {a...}, output: {b ... }},...]" |
| 19 | **The body of an `each` is a child invocation, and it passes its params with `with:`** (the one way). No special per-row form. | "the value for each is the child invocation and uses with to pass params" |
| 20 | **"decider" is a user-defined name, not part of the schema.** The schema must not have a `decider:` keyword; outputs are named by the sketch's author. | "I think 'decider' is a user defined name not part of the schema definition" |

## Decided by Claude while the owner was asleep (2026-10-30), for the owner to review

The owner said: "do your best to finish without me. It is done when there is nothing left to take away." Each choice below took the smaller option. Overturn any of them.

| # | Choice | Why (what it takes away) | Drew's Response |
|---|---|---|
| A | A final state's `outputs:` is a plain list of names: `outputs: [temp]`. The `decider:` wrapper is gone. | Decision 20 (no `decider` keyword); reuses the names of `outcomes:`. | agreed |
| B | A `blend` entry that uses a subsketch's rows is `- from: weather`, not `- decider: weather`. | Decision 20; `from:` already means "this other thing" in a Jev source's `state:`. | i'm not sure what blend has to do with from but we can keep it for now while we consider if this is part of an "aggregators" feature or an etl step |
| C | Inside an `each`, the row's fields are the child's variables by their own names; `with:` still passes anything extra, as everywhere. | Decision 19 says `with:` passes params; naming each row field in `with:` would repeat what the row already says. | ok |
| D | A loop's child may declare outputs the parent has no outcome for, because the loop's result is pairs, not weights to blend. | Decision 18. | seems resonable but could be subjectg to change in the future|
| E | A child inside an `each` is read with its row values left empty when the parent is checked (the child is checked on its own). | Decision 6 (encapsulation). | +1 | 
| F | A row's Jev answers are captured under `<child name>[<row position>]`, so replay needs no new mechanism. Replay does not list those keys up front. | Reuses capture/replay as is. | yay |

## Still open

1. **How an output that is not weights is declared** (a `hold`, a film's audience level). With A, a child lists names; the options of an output are not yet declared anywhere but the parent's `outcomes:`.
  1. [Drew] this could be something like a sketch type but lets wait and see if there are more than 1.  I think we'll uncover some of this as we work through more examples later on.  try to design a flexable seam for now so we can try out a few options down the road. just don't overcomplicate it.
2. **What `docs/DOMAIN.md` calls a "decider"** should be reviewed against decision 20; the word is only prose now.
  2. [Drew] See above.  @morph what to you recommend for the model here (wrt. BDD and Domain Abstraction)

### Morpheus's recommendation on open item 2 (domain abstraction and BDD), for the owner to accept or reject

**Recommendation: retire "decider" as a domain term, and let the consumer define what an output must look like.**

* **What the model needs is two ideas, not three.** *Decision Row* (one combination of outcome values and a weight) is a thing a stage produces. *Blend* is the policy that combines them. "Decider" named only the role a stage plays while producing Decision Rows; it added a type with no behaviour of its own, and it leaked into the schema (`decider:` twice). `DOMAIN.md` now has no Decider entity, a new **Output** (a name a final state lists), and Blend defined over Decision Rows.
* **The seam is the output name plus the consumer's check.** A sketch's `outputs: [names]` is the whole contract on the child's side. The *consumer* decides what it accepts and checks at its own boundary: `blend` requires Decision Rows over declared outcomes (checked at `check` time by name, and at run time by `_validate`); `each` accepts anything and pairs it with its input row. A new kind of output (a `hold`, a film's audience level) then needs only a new consumer that knows how to read it, not a change to the child's declaration. That is the flexible, uncomplicated seam item 1 asked for, and nothing is added now.
* **BDD, as the acceptance language for this seam** (these become the tests of UND-73 and UND-69):
  * *Given* a child that outputs `[audience]` and a parent that `blend`s `from` it, *when* the child's rows name an option the parent has not declared, *then* `check` or the run fails naming the stage and the option.
  * *Given* a parent that runs the child `each` film, *when* the run finishes, *then* the result is one `{input, output}` pair per film, in the films' order, with nothing merged.
  * *Given* a child that declares no `outputs`, *when* the parent blends from it, *then* `check` refuses it by name.
* **What this costs:** nothing in code (no `Decider` class existed); only the domain document and the prose that said "decider".

Owner's reply: _(accept / change)_

## Working tree

Phase 1 code is committed (`ef98618`, 179 Python tests, lint clean).
