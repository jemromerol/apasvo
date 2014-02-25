#!/bin/sh

for file in *.qrc
do
    output_file="qrc_${file%.*}.py"
    pyside-rcc "$file" -o "$output_file"
    mv "$output_file" ../eqpickertool/gui/views/generated
done

