dist_dir="dist"
output="apasvo"
spec_dir="installer"
scripts=("apasvo-gui" "apasvo-detector" "apasvo-generator")

output_dir="$dist_dir"/"$output"
rm -rf "$output_dir"
mkdir "$output_dir"
for script in "${scripts[@]}"
do
    pyinstaller "$spec_dir"/"$script".spec
    script_dir="$dist_dir"/"$script"
    cp -rf "$script_dir"/* "$output_dir"
    rm -rf "$script_dir"
done

