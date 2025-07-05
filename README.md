# fuzzy_parser
parse json files given path with little bit of variation in the key value.

# Usage
```python
import fuzzy_parser
payload = fuzzy_parser.load_payload(r"Z:\Documents\TASKS\readpl\test.json")
result = fuzzy_parser.parse_mapping("stud_ents/Name", payload)
print(result)
```
```
students/[0]/name=Jim
students/[1]/name=Dwight
students/[2]/name=Kevin
```

```test.json
{
    "school_name": "Dunder Miflin",
    "class": "Year 1",
    "students": [
        {
            "id": "A1",
            "name": "Jim",
            "math": 60,
            "physics": 66,
            "chemistry": 61
        },
        {
            "id": "A2",
            "name": "Dwight",
            "math": 89,
            "physics": 76,
            "chemistry": 51
        },
        {
            "id": "A3",
            "name": "Kevin",
            "math": 79,
            "physics": 90,
            "chemistry": 78
        }
    ]
}
```
