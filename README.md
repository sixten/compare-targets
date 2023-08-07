# compare-targets

This is a simple script that compares the contents and configuration of two targets within a single Xcode project.

The original use case was an product where we had to maintain several dozen white label versions of the app in addition to the core multi-tenant app. With several different people adding, updating, and changing those alternate version at the same time as ongoing development, ensuring that all of the targets were kept in sync became an important consideration.

There's nothing all that earth-shattering going on here: the code leverages the `pbxproj` package to parse and examine the structure of the project. It walks through each of the targets and builds a simpler in-memory representation of the specific information we care about. That information is then written to a pair of temporary JSON files so that it can leverage [Beyond Compare](https://www.scootersoftware.com) (or your favorite alternate diffing tool) to perform the comparison.

This script will fall back to FileMerge as a last resort, but with our app, the length of the JSON files sometimes exceeded the maximum text that FileMerge could handle. Your mileage may vary.
