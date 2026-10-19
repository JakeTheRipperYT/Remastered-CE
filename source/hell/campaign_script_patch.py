from pathlib import Path
import sys, json
W=Path(__file__).resolve().parent
import argparse
parser=argparse.ArgumentParser()
parser.add_argument('original',type=Path,help='Locally extracted campaigns/jap_shogun/scripting.lua')
parser.add_argument('output',type=Path)
args=parser.parse_args()
original=args.original.read_bytes()
text=original.decode('utf-8')
nl='\r\n' if '\r\n' in text else '\n'
anchor='local BOOL_dif_very_hard = false'
assert text.count(anchor)==1
text=text.replace(anchor,anchor+nl+'local BOOL_dif_hell = false')
anchor='\t\t\tBOOL_dif_legendary = true'
assert text.count(anchor)==1
text=text.replace(anchor,anchor+nl+'\t\telseif conditions.DifficultyLevel(context) == -4 then'+nl+'\t\t\tout.ting("Playing on Hell.")'+nl+'\t\t\tBOOL_dif_hell = true')
anchor='elseif BOOL_dif_very_hard or BOOL_dif_legendary then'
assert text.count(anchor)==9
text=text.replace(anchor,'elseif BOOL_dif_very_hard or BOOL_dif_legendary or BOOL_dif_hell then')
lines=text.splitlines(keepends=True)
for needle,addition in [
 ('save_named_value("BOOL_dif_very_hard",','\tscripting.game_interface:save_named_value("BOOL_dif_hell", BOOL_dif_hell, context)'),
 ('load_named_value("BOOL_dif_very_hard",','\tBOOL_dif_hell = scripting.game_interface:load_named_value("BOOL_dif_hell", false, context)')]:
    indices=[i for i,line in enumerate(lines) if needle in line]
    assert len(indices)==1
    lines.insert(indices[0]+1,addition+nl)
modified=''.join(lines).encode('utf-8')
args.output.write_bytes(modified)

