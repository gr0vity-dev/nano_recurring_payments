// custom javascript

(function() {
  console.log('Sanity Check!');
})();

function handleClick(type) {
  fetch('/tasks', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ type: type }),
  })
  .then(response => response.json())
  .then(data => getStatus(data.task_id));
}


function getStatus(taskID) {
  fetch(`/tasks/${taskID}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json'
    },
  })
  .then(response => response.json())
  .then(res => {
    const html = `
      <tr>
        <td>${taskID}</td>
        <td>${res.task_status}</td>
        <td>${res.task_result}</td>
      </tr>`;
    const newRow = document.getElementById('tasks').insertRow(0);
    newRow.innerHTML = html;

    const taskStatus = res.task_status;
    if (taskStatus === 'SUCCESS' || taskStatus === 'FAILURE') return false;
    setTimeout(function() {
      getStatus(res.task_id);
    }, 500);
  })
  .catch(err => console.log(err));
}


function post_faucet(type, seed) {
  console.log(seed)
  fetch('/faucet', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ type: type, seed : seed }),
  }).then(response => console.log(response.json()));
}

// function post_faucet(type, seed, nano_address) {
//   fetch('/faucet', {
//     method: 'POST',
//     headers: {
//       'Content-Type': 'application/json'
//     },
//     body: JSON.stringify({ type: type, seed : seed }),
//   })
//   .then(response => response.json())
//   .then(data => sse_faucet_status(data.task_id, nano_address));
// }


// function sse_faucet_status(taskID, nano_address) {
//   fetch(`/faucet_status`, {
//     method: 'POST',
//     headers: {
//       'Content-Type': 'application/json'
//     },
//     body: JSON.stringify({ task_id: taskID, nano_address : nano_address }),
//   })
// }
