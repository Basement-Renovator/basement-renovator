# Basement Renovator

This project was bootstrapped with [Create React App](https://github.com/facebook/create-react-app).

## Developing

- Electron/Chromium's structure ensures the application runs across two processes:
  - The *main/browser* process is responsible for creating and managing application windows
  - The *renderer* processes each correspond to a window and are responsible for essentially running a given web app
- `src/index.js` - All UI and business logic running in a *renderer* process; edit this for most development purposes
- `src-main/index.js` - All *browser* process configuration and creation of the window
- `src-preload/index.js` - All preload code running just before the *renderer* process is split from the *main* process

## Available Scripts

In the project directory, you can run:

### `yarn start`

Runs the app in the development mode.

### `yarn test`

Launches the test runner in the interactive watch mode.\
See the section about [running tests](https://facebook.github.io/create-react-app/docs/running-tests) for more information.

### `yarn build`

Builds the app for production to the `build` folder.\
It correctly bundles React in production mode and optimizes the build for the best performance.

The build is minified and the filenames include the hashes.\
Your app is ready to be deployed!

See the section about [deployment](https://facebook.github.io/create-react-app/docs/deployment) for more information.