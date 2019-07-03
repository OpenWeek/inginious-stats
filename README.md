# inginious-stats
Plugin INGInious to improve stats view in the course administration

## Installing
### Editable mode

Clone the repo. Then, to install the plugin in editable mode, execute the following command from inside the repo you cloned:

    pip3 install -e .

### Non-editable mode
You will need to uninstall and reinstall the plugin every time you make a change to the sources.

    pip3 install git+https://github.com/OpenWeek/inginious-stats

## Activating

In your ``configuration.yaml`` file, add the following plugin entry:

    plugins:
      - plugin_module: "inginious-stats"

**After making a change**: restart the webapp and this should work. (If you didn't install the package in editable mode, you will need to reinstall it.)

## Intended features
Filter per:
- all submissions/best submissions/100% submissions
- tags
- exerciseId
- student
- ignore submissions with certain gradings

Type of charts:
- plot distribution of grades for submissions
    - basic statistics (mean, variance, standard deviation, median, mode...)
- number of submission before 100%
    - basic statistics (mean, variance, standard deviation, median, mode...)
- number of lines / submission
    - basic statistics (mean, variance, standard deviation, median, mode...)

Feature:
- export to CSV

