#!/bin/bash

#======
# Copyright (c) IBM Corp. 2011, 2014.
# All rights reserved. This program is made available
# under the terms of the Eclipse Public License v1.0
# which accompanies this distribution, and is available at
# http://www.eclipse.org/legal/epl-v10.html
#======


# =====================================================================
# apply-copyright.sh - Apply Copyright to source files (.sh .py)
#
# search strings suposed to be at the first line on files starting on src folder
# (1) Matching cases for #! (shebang): keep whole line + substitute end of line (EOL) with Copyright text
# (2) Matching cases for # -*- (Python Enconding) : idem 
# (3) No matching cases: include Copyright text at the begining of the file

i18n_STR="# -\*-"
STR_BASE="#!"
END_OF_LINE="$"
PRE_TEXT="\n\n"
COPYRIGHT_TEXT="#======\n# Copyright (c) IBM Corp. 2011, 2014.\n# All rights reserved. This program is made available\n# under the terms of the Eclipse Public License v1.0\n# which accompanies this distribution, and is available at\n# http:\/\/www.eclipse.org\/legal\/epl-v10.html\n#=======\n\n" 

#(1)
grep -lr --include="*.py" --include="*.sh" --exclude="apply-copyright.sh" -e '#!/' ./src | xargs sed -i '/'"$STR_BASE"'/ s/'"$END_OF_LINE"'/&'"$PRE_TEXT$COPYRIGHT_TEXT"'/g'

#(2)
grep -lr --include="*.py" --include="*.sh" --exclude="apply-copyright.sh" -e '# -\*-' ./src | xargs sed -i '/'"$i18n_STR"'/ s/'"$END_OF_LINE"'/&'"$PRE_TEXT$COPYRIGHT_TEXT"'/g'

#(3)
grep -Lr --include="*.py" --include="*.sh" --exclude="apply-copyright.sh" -e '#!/' -e '# -\*-' ./src | xargs sed -i '1i'"$COPYRIGHT_TEXT"''

# ========================================================================
