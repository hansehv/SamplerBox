#!/bin/sh
echo perform next command from command line:
echo gcc -Wall -Wextra -O -ansi -pedantic -fpermissive -shared interface.cpp -o interface.so
# test compile separate modules: gcc -Wall -Wextra -O -ansi -pedantic -fpermissive -shared module.cpp -lpthread -lm
# no -o necessary, you will end up with an a.so
