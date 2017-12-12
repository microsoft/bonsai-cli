# Changelog

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
