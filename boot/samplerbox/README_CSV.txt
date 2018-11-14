General remarks the csv files:
- Delimiters can be comma, semicolon or tab
- Quotes and space are ignored
- So you cannot use above characters in names
- A field starting with # means this field plus following are comments
- Rows containing syntax errors will be ignored (with error messages)
- Error messages are printed when the script is run manually

Syntax of midi_controllers.csv:
- Headings!
- Column1: Controller name
- Column2: The control change this controller sends
- Column3: The value sent by this controller (this is often configurable)
     Value -1 indicates a continuous controller (wheel, pot, drawbar)

Syntax of midi_mapping.csv:
- Headings!
- Controller: name as defined in midi_controllers.csv (this is the link)
     You can, but do not have to, list all defined controllers here
     UA=unassigned means no controller is set to the function mapped in this row
- Next columns refer to internal functions/values.
  Don't change or delete them !!!
- Type: this a kind of category.
    - Fixed: internal hardcoded function (name in next column)
    - Backtracks: depends on the backtracks defined in active preset.
    - Chords: defined in the chords.csv (see below)
    - Scales: defined in the scales.csv (see below)
    - Voices: depends on the voices defined in active preset.
    - UA=unassigned: to be used when you don't assign a controller
- Sets: depends on the type
    - Fixed: function that will be called using the value (Col3 of midi_controllers)
    - Others: value, depending on type: voice#, backtrack#, chordname, scalename
- Mode: how the samplerbox treats this function
    - Continuous: accepts values 0-127
    - Switch: will set function on when receiving value and off when receiving 0.
    - Toggle: will set function on when receiving value and off on next receive value
    - SwitchOn: will set function on when receiving value
    - SwitchOff: will set function off when receiving value

Syntax of chords.csv:
- No headings!
- Column1: chordname
- Next columns give displacement of notes to be played, based from the original note.
  So column2 is mostly 0 (but you may have creative ideas :-)
  Yes, also negative values are allowed...
- only positive values are allowed

Syntax of scales.csv:
- Headings!
- Column1: scalename
- Next 12 columns give chords to played when heading note is played
  These chords have to be defined in the chords.csv
- Values 0 or - mean single note
- You must fill 12 note values !! The samplerbox will run, but misbehave otherwise
