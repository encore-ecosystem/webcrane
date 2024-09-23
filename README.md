# WebCrane
Old name is wsvcs (WebSockets Version Control System)
  
## Description
This project resolve the git's restriction about 100mb of commit size. We use the following idea: wsvcs will "chunkify" every file that you want to share with coloborators.    

## Getting Started

### Dependencies
- Python 3.12
- Windows (Tested only between win2win case)

### Installing
```bash
git clone https://github.com/encore-ecosystem/webcrane.git
cd webcrane
pip3 install .
```
### Executing program
```
webcrane <option>
option:
- init
- deploy
- push
- pull
- cli
```

## Version History
* 0.1
    * Initial Release
* 0.2
    * Add dotignore support (without whitelist)
    * Boosting working speed
    * Fixing bugs
* 0.3
    * Add colored progress bars
    * Multithreaded hashing
* 0.4
    * New peer logic
    * More info in progress bars
    * Updated algorithms

## License

This project is licensed under the MIT License - see the LICENSE.md file for details

## ToDo:
- Logging
- Merging support
