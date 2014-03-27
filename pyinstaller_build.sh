dist_dir="dist"
output="eqpickertool"
scripts=("detectorgui" "detector" "generator")

output_dir="$dist_dir"/"$output"
rm -rf "$output_dir"
mkdir "$output_dir"
for script in "${scripts[@]}"
do
    pyinstaller "$script".spec
    script_dir="$dist_dir"/"$script"
    cp -rf "$script_dir"/* "$output_dir"
    rm -rf "$script_dir"
done

