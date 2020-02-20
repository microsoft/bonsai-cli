# Changelog

## 0.9.10
- #11789: Require bonsai-ai 2.2.9 (store auth tokens in the platform keystore)

## 0.9.9
- #14057: Fix for websocket test in bonsai diagnose
- #13700: Fix for bonsai create pushing an incorrect project file to service

## 0.9.8
- 13066: Print request headers in debug mode

## 0.9.7
- #13069: Perform CLI version checks with PyPI asynchronously
- #12837: Use the same python executable when testing websocket in bonsai diagnose
- Add debug log to api requests
- #12833: Add new checks for invalid .bonsai files in bonsai diagnose
- #13277: Improve NotAllowListed error reporting during bonsai configure 

## 0.9.6
- #12658: require bonsai-ai 2.2.5 (stores workspace only in .bonsai file)

## 0.9.5
- #12423: Remove legacy auth support in CLI

## 0.9.4
- #12576: Switch out click.prompt with STL input

## 0.9.3
- IcM/141829256: CLI is writing the .aadcache file to the local directory.
- #12492: Include function to validate AAD bearer token in `bonsai diagnose`
- #12513: Replace pip get_installed_distributions import with safer setuptools import

## 0.9.2
- #12458: Require bonsai-ai version 2.2.1 or greater

## 0.9.1
- #12454: Correct URL paths printed in `bonsai configure`

## 0.9.0
- #12367: Configure should default to AAD behavior and not accept username
- #12344: Configure with AAD should auto-populate profile workspace
- #12345: Fix for create to switch to AAD after receiving BonsaiAuthDeprecated
- #12346: Commands should switch to AAD after receiving BonsaiAuthDeprecated or InvalidUseOfAccessKey
- #12348: Add bonsai logout command to clear AAD cache
- #12230: Fix typo in Connection Error message

## 0.8.37
- #11673: Added RequestId header to all requests
- #11815  Aria telemetry
- #11926: Added python >=3.5 as a requirement to install the cli
- #12116: Move telemetry blacklist logic into AriaWriter class
- #12094: Add -a/--aad flag to use AAD authentication
- #12130: Skip Aria Writer teardown due to deadlock in special cases

## 0.8.36
- Pyright bugs

## 0.8.35
- #10046: Fix pip import in cli for newer version of pip
- #10533: Request timeouts should not show a stack trace
- #10623: Fix file too large tests

## 0.8.34
- #7858: Bonsai diagnose unit tests
- #9617: Print clean error message on JSON decode errors

## 0.8.33
- #7848: Bonsai diagnose exits gracefully if user is not connected to internet
- #7654: Print useful message when SSL errors occur during version check
- #7802: Add short aliases to all options in cli

## 0.8.32
- #7666: Fix bonsaicli unit tests windows
- #6694: Remove warning spam in config
- #7408: Fix bug in bonsai diagnose

## 0.8.31
### Added
- Every command will check if bonsai is up to date. It can be disabled using `bonsai --disable-version-check [COMMAND]`
### Changed
- Change value written to config for `use_color`
- `bonsai push` works with relative paths specified in `projectfile`
- catch subprocess error and print output for `bonsai diagnose`
- update setup.py requirements
- Allow brains in error state to start training
- Fixed bug in `utils.py` where `Config` was taking in cli command-line args

## 0.8.30
## Added
- `bonsai diagnose` runs various tests to check the health of `bonsai-cli`
-  Added `get_project` to API.
-  Added `utils.py` file
### Changed
- Updated `bonsai train status` to now print config profile and file location(s)
- Moved various functions into `utils.py`

## 0.8.29
### Changed
- Improved loading of proxy settings.
- Updated sims list output to reflect the changes to the API
- `bonsai switch` and `bonsai switch --show` print configuration file location

## 0.8.28
- Removed PPC64 references.

## 0.8.27
### Changed
- Update `bonsai create` so that check for existing brain name uses brain
  details api instead of list brains api
- Removed calls to `os.path.samefile` in projfile because it was not supported in a windows/python2.7 environment. Added a helper function `_samefile` to emulate `os.path.samefile`

## 0.8.26
## Added
- Added top level `--enable-color/--disable-color` option to enable/disable color printing in the cli
- Added more logs to the cli

### Changed
- Remove redundant message on `bonsai configure`
- Fixed cli behavior with `DEFAULT` profile
- `bonsai push` and `bonsai create` prevent users from pushing files with a size greater than 640KB
- `bonsai create` prints error message if BRAIN is in 'ERROR' state
- Remove console prints on successful `bonsai train start/stop/resume` attempts
- Remove console prints on successful `bonsai create/delete`
- Updated cli logging to use bonsai-ai logger
- CLI errors will be printed in red if color is enabled

## 0.8.25
- Update bonsai configure for new validate endpoint
- Make testing logs quieter
- use raw_input with python2, input is okay with python3
- update http to https for all setup.py

## Added
- `--username` option for configure

### Changed
- `bonsai configure` prompts for username and access key
- `--key` option for configure changed to `--access_key`

## 0.8.24
### Changed
- `bonsai push` fails and prints error message while brain is training

## 0.8.23
### Added
- `--sysinfo` top level option to print system information
- `--timeout` top level option to modify api request timeout time

### Changed
- CLI unittests preserve local .bonsai

## 0.8.22
### Added
- Added `--json` flags to various commands
- `bonsai switch --show` prints active profile information
- `bonsai configure --show` prints active profile information

### Changed
- `bonsai switch -h/--help` prints available profiles and marks active profile if one exists
- 'bonsai-config' replaced with sdk2 config

## 0.8.21
### Added
- Added `bonsai train resume [--remote]`

### Changed
- 'bonsai push' prints inkling errors.

## 0.8.19
### Added
- Added `bonsai pull`.
### Changed
- `bonsai push` now lists the names of files that were pushed.
### Fixed
- `bonsai log --follow` for Python 3.5.x.

## 0.8.18
### Changed
- Validates project JSON before creating or pushing project files.

## 0.8.17
### Changed
- Lint fixes

## 0.8.16
### Changed
- Added '-h' as another option for '--help' for all commands
- Added top level 'help' command to cli
- Added version checking to the --version option

### Added
- The ability to delete BRAINs from the command line.

## 0.8.15
### Added
- Better error reporting for connection errors and redirects
- Additional output messages regarding default BRAIN
- Changed user message
- Allows for Unix-style globbing in project file file lists
- Allows http_proxy, https_proxy and all_proxy to configure websockets

### Changed
- API client code to upload project files with MIME type `application/octet-stream`
- Default project file to include both `.ink` and `.py` files

## 0.8.14
### Added
- Add tests for bonsai configure

## 0.8.13
### Changed
- Changed the web endpoint for access key retrieval

## 0.8.12
### Changed
- Simplify pytest settings

## 0.8.11
### Fixed
- Fix `bonsai log` truncation on windows

## 0.8.10
### Added
- Add the `--follow` flag to the `bonsai log` command.
- Add dependency on the 'websocket-client' pip package to support the
new `--follow` flag.
- Add this changelog file.

### Removed
- Remove the `bonsai load` command. The `bonsai push` command should be
used instead.

## 0.8.9
### Removed
- Remove nose2 config file.

## 0.8.8
### Added
- Add missing help message for `bonsai train start --remote`.
- Add a short help command for `bonsai log`.

## 0.8.7
### Fixed
- Fix an issue where a project file was uploaded with its local absolute
path instead of a path relative to the project root.

## 0.8.6
### Added
- Add the `bonsai log` command.

## 0.8.5
### Fixed
- Fix an issue that could cause file not found errors when using the
`--project` option with the `bonsai create` and `bonsai push` commands.

## 0.8.4
### Added
- Add the `bonsai push` command.

### Deprecated
- The `bonsai load` command is now deprecated. Use `bonsai push` instead.

## 0.8.3
### Fixed
- Include Content-Length header when sending multipart/mixed requests.

## 0.8.2
### Added
- Add the `--project-type` option to the `bonsai create` command.
- Add short help messages for some commands.
- Add functionality to `bonsai create` to upload all project files by
  specifying a multipart/mixed request.
- Add the `bonsai download` command.

## 0.8.1
### Fixed
- Fix an issue that could cause the file order in project files to
  change non deterministically.

## 0.8.0
### Removed
- Remove the `bonsai brain create` command.

## 0.7.1
### Fixed
- Fix a python 2.7 incompatibility in project files.

## 0.7.0
### Added
- Add initial project file support.

### Changed
- Modify the `bonsai create` command to create a project file.
- Modify the `bonsai load` command to find the inkling file to upload
  from the contents of the project file.

## 0.6.2
### Fixed
- Fix a python 2.7 incompatibility in dot brains files.

## 0.6.1
### Changed
- Use click's simple table format instead of fancy_grid.

## 0.6.0
### Added
- Add support for dot brains files to cache brain names, and refactor
  many commands to utilize this. See the Changed section just below for
  more specific information.

### Changed
- The `bonsai brain load` command is now just `bonsai load`.
- The `bonsai brain train` parent commands are now just `bonsai train`, and
  specifying the name of the brain is now optional with the `--brain` flag.
- The `bonsai create` command sets the specified brain name as default.
- Many other commands that used to require the brain name have been changed
  to allow specifying the brain name optionally using the `--brain` flag,
  such as the `bonsai sims` command.

## 0.5.2
### Added
- Add the `bonsai switch` command for working with multiple profiles in
a bonsai config file.
- Add the `--json` flag to the `bonsai train status` command.
- Add the `--key` flag to the `bonsai configure` command.

### Changed
- Increase the minimum required version of bonsai-config to 0.4.0.

## 0.5.1
### Changed
- Made a change to the `bonsai train status` command so that it's output
more accurately reflects the response of the underlying HTTP API.

## 0.5.0
### Changed
- Moved HTTP API calls out into their own object for better code organization.

## 0.4.2
### Added
- Add functionality using pypandoc to convert README.md to RST.

## 0.4.1
### Added
- Add python 2.7 support.

## 0.4.0
### Added
- Initial public release.
