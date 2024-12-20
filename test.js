import http from 'k6/http';

export default function () {
    let url = 'http://localhost/classify';
    let payload = JSON.stringify({ url: "https://img-cdn.pixlr.com/image-generator/history/65bb506dcb310754719cf81f/ede935de-1138-4f66-8ed7-44bd16efc709/medium.webp" });
    let params = { headers: { "Content-Type": "application/json" } };
    http.post(url, payload, params);
}
