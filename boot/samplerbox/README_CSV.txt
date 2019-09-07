General remarks the csv files:
- Delimiters can be comma, semicolon or tab
- Quotes and space are ignored
- So you cannot use above characters in names !!
- A field starting with # means this field plus following are comments
- Rows containing syntax errors will be ignored with error messages
- These error messages are displayed when the script is run manually
-----------------------------------------------------------------------------------
Syntax of controllerCCs.csv:
- Headings!
- Controller: Controller name
- CC: The control change number this controller sends
- Val: The value for this control change sent by this controller (this is often configurable)
     Value -1 indicates a continuous controller (wheel, pot, drawbar)
This list will be appended with the notenames as defined in keynotes.csv:
  The controller name is this notename
  The CC of these notes is defined in the configuration.txt via NOTES_CC
  The Val is the notenumber (so C4 sends CC=60, but this is transparant for you)
  All this to facilitate the "Ctrl" in the notemaps
  It requires the optional keynotes.csv
---- ==> the distributed file showes my setup, you should adapt that to your equipment
-----------------------------------------------------------------------------------
Syntax of CCmap.csv:
- Headings!
- Controller: name as defined in midi_controllers.csv (this is the link)
     You can, but do not have to, list all defined controllers here
     UA=unassigned means no controller is set to the function mapped in this row
- Next columns refer to internal functions/values (see Controls.csv for overview)
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
---- ==> the distributed file showes my setup, you should adapt that to your equipment
---- ==> the CCmap.csv in sampleset directory has an extra leftmost column: <== ---
- Voice: to which voice this override (change or addition) applies:
    - 0: applies to all voices in this set except when an explicit voice override is also specified)
    - 1-127: override this voice only
---- ==> Controls.csv gives values of all implemented functions
-----------------------------------------------------------------------------------
Syntax of keynotes.csv (optional, if omitted, note mapping can only be done via midinotes):
- Headings!
- Key: Desired name of the midisensor (key, snare, pad..)
- Midinote: note sent by this midisensor
- Drumpad Midinote: optional, this note on channel 10 will be translated to Midinote on active channel (default 1)
---- ==> keynotes-examples.csv showes some examples
-----------------------------------------------------------------------------------
Syntax of chords.csv:
- No headings!
- Column1: chordname
- Next columns give displacement of notes to be played, based from the original note.
  So column2 is mostly 0 (but you may have creative ideas :-)
  Yes, also negative values are allowed...
- only positive values are allowed
-----------------------------------------------------------------------------------
Syntax of scales.csv (only works in 12-tone scales):
- Headings!
- Column1=Scale: scalename
- Next 12 columns give chords to played when heading note is played
  These chords have to be defined in the chords.csv
- Values 0 or - mean single note
- You must fill 12 note values !! The samplerbox will run, but misbehave otherwise
