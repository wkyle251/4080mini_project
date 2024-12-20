url: localhost:80
method: get
return : html

url: localhost:80
method: post
request body:
{
    "file": file_object(required = False),
    "image_url": String(required = False),
}
return : json
{
    "status": string,
    
}



