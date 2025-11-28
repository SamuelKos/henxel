#!/usr/bin/env bash


if [[ "$#" -gt 1 ]]; then
  echo "Illegal number of parameters"
  exit 1
elif [[ "$#" -eq 1 ]]; then
  if [[ $1 -eq mainloop ]]; then
    echo "Starting debug in mainloop"
    until python -m henxel --debug; do
      echo "Restarting Editor.." >&2
      sleep 1
    done
    exit 0
  else
    echo "Starting debug"
    until python -i -c "import henxel;e=henxel.Editor(debug=True)"; do
      echo "Restarting Editor.." >&2
      sleep 1
    done
    exit 0
  fi
else
  echo "Starting debug"
  until python -i -c "import henxel;e=henxel.Editor(debug=True)"; do
    echo "Restarting Editor.." >&2
    sleep 1
  done
  exit 0
fi


#until python -i -m henxel; do
until python -i -c "import henxel;e=henxel.Editor(debug=True)"; do
  echo "Restarting Editor.." >&2
  sleep 1
done
exit 0
















