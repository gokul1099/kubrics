"use client";
import React from "react";
export default function VideoUpload() {
  const [videoUrl, setVideoUrl] = React.useState("")
  const handleVideoUpload = async(event: React.ChangeEvent<HTMLInputElement>)=>{
    
    const file = event.target.files?.[0]
    if(file){
      try{
        const formData = new FormData()
      formData.append('file',file)

      const uploadResponse = await fetch('http://localhost:8080/upload-video', {
        method:"POST",
        body: formData
      })

      if(!uploadResponse.ok){
        console.log(uploadResponse, "response from upload")
        throw new Error('Failed to upload')
      }
      }catch(e){
        console.log("Error in video uploading", e);

      }
      
    }
  }
  
  console.log(videoUrl,"vi")
  return (
    <aside className="fixed right-0 top-0 h-full w-96 border-l border-gray-200 shadow-lg p-6 z-30">
      {
        !videoUrl && <input type="file" className="bg-red-400 border-1" onChange={(e)=>handleVideoUpload(e)}/>
      }
      
      {
        videoUrl && 
        <video src={videoUrl} controls height={400} width={400} className="border-2 border-white"/>
      }
      
      {
        videoUrl && <button onClick={()=>setVideoUrl("")} className="border-2 border-white mt-20">Remove Video</button>
      }
      
    </aside>
  );
}
