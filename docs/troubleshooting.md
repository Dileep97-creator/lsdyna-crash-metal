# Troubleshooting

Solver errors that point somewhere other than the actual cause, and what
they really mean.

## Thousands of "invalid material" errors on elements that are fine

```
*** Error 20388 (STR+388)
    thin shell element 331
    has an invalid material 1
    that exceeds the number of materials defined, 0
*** Error 20389 (STR+389)
    thin shell element 331 references part number 1
    that does not reference a thin shell section
```

The elements are not the problem. "Materials defined, 0" is the real
message: the solver never read any `*MAT` or `*SECTION` card at all, so
it fell back to treating each element's part ID as a material index.

The cause is an `*END` inside a file pulled in with `*INCLUDE`. `*END`
terminates input reading, so everything the parent deck defines after the
`*INCLUDE` line is dropped in silence - sections, materials, contacts,
boundary conditions, the lot. The nodes and elements are read correctly,
which is why the errors land on them.

Two rules follow, and both are now enforced:

1. **An include file carries no `*KEYWORD` and no `*END`.**
   `tools/kfile.py` writes include files through `Deck(..., include=True)`,
   which omits both, and `tools/validate_k.py` fails any file that is an
   `*INCLUDE` target and still contains either.

2. **Put the `*INCLUDE` last in the parent deck.** If an include ever
   misbehaves - a hand-edited mesh, a `dynain` written by the solver,
   which does end with `*END` - everything above it has already been
   read, so the failure is bounded instead of silently gutting the model.

This is worth internalising beyond this repository. Any time a deck
produces a huge, uniform block of errors about elements, read the *count*
in the message rather than the element numbers. "0 materials defined" or
"0 sections defined" means the reader stopped early, and the place to
look is the last thing it read successfully, not the first thing it
complained about.

## An error that blames the keyword *after* the broken one

```
*** Error 10246 (KEY+246)
    line contains improperly formatted data
     reading *CONTROL_CONTACT
         At line# 25
--------------------------------------------------------------------------
*CONTROL_ACCURACY
--------------------------------------------------------------------------

*** Error 10450 (KEY+450)
    in keyword command:
        1         4         0         1
```

Read it carefully: the reader is *inside* `*CONTROL_CONTACT` and the line
it choked on is `*CONTROL_ACCURACY`. Nothing is wrong with
`*CONTROL_ACCURACY`. `*CONTROL_CONTACT` takes two mandatory cards, only
one was supplied, so the reader went looking for the second one and
swallowed the next keyword line as data. Having lost its place, it then
treated the following data card as a keyword command, which produced the
second error.

A missing card never announces itself. It corrupts whatever comes next,
and the error you get names the innocent party. Whenever an error says
"reading *X" but quotes a line belonging to *Y, the fault is in *X's card
count.

`tools/validate_k.py` now carries a table of mandatory card counts for
every keyword this repository emits and fails any block that is short.

## Two numeric fields with no space between them

```
$#     mid        ro         e        pr
         20.00694444     210.0       0.3
```

That is `mid = 2` in columns 1-10 and `ro = 0.00694444` in columns 11-20.
It is legal fixed format and the solver reads it correctly, but it is
unreadable and impossible to check by eye, and it hides genuine overflow.
`kfile.fmt` now formats floats into one column narrower than the field so
there is always a separator.

## Where to look first when a run dies at initialisation

In order, because each is cheaper than the one after it:

1. `python3 tools/validate_k.py <deck> <its includes>` - field overflow,
   duplicate IDs, dangling references, short keyword blocks, include-file
   violations.
2. The **first** error in `messag`, not the last, and the counts inside
   the message rather than the entity numbers.
3. `d3hsp` - the echo of what the solver actually parsed. The keyword
   count list near the top is the fastest check there is: if
   `*MAT_option`, `*SECTION_option` or `*PART_option card` reads zero,
   the reader stopped before reaching them, and the question is what
   stopped it rather than what it complained about.
4. `python3 tools/mesh_quality.py <mesh>` - degenerate elements and the
   critical timestep, if the run started and then collapsed rather than
   failing to initialise.
