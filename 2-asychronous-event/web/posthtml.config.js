module.exports = {
    plugins: {
      "posthtml-expressions": {
        locals: {
          WEBSOCKET_URL: process.env.WEBSOCKET_URL
        }
      }
    }
  };