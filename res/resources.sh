#!/bin/sh

for file in *.qrc
do
    output_file="qrc_${file%.*}.py"
    pyrcc4 "$file" -o "$output_file"
    mv "$output_file" ../apasvo/gui/views/generated
done

