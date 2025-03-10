export function test(){
    console.log("Testas!!!")
}

function getHost(){
    return "http://localhost:8002";
    // return "..";
}

export async function getSegmentsData(file_name) {
    const url = `${getHost()}/elan-file/files/${file_name}`;
    try {
        const response = await fetch(url);
        if (!response.ok) {
          throw new Error(`Response status: ${response.status}`);
        }
    
        const json = await response.json();
        return json;
    } catch (error) {
    
    }
}

export async function getDiffData(file_name) {
    console.log("Host", getHost());
    
    const url = `${getHost()}/elan-file/files/${file_name}/diff`;
    try {
        const response = await fetch(url);
        if (!response.ok) {
          throw new Error(`Response status: ${response.status}`);
        }
    
        const json = await response.json();
        return json;
    } catch (error) {
    
    }
}

export async function getDiarizationErrorRate(file_name) {
    console.log("Host", getHost());
    
    const url = `${getHost()}/elan-file/files/${file_name}/segment/diarization_error_rate`;
    try {
        const response = await fetch(url);
        if (!response.ok) {
          throw new Error(`Response status: ${response.status}`);
        }
    
        const json = await response.json();
        return json;
    } catch (error) {
    
    }
}

export function getDiffDataCsvUrl(file_name) {
    const url = `${getHost()}/elan-file/files/${file_name}/diff/csv`;
    return url;
}

export async function getDiffDataCsv(file_name) {
    console.log("Host", getHost());
    
    const url = getDiffDataCsvUrl(file_name)
    try {
        const response = await fetch(url);
        if (!response.ok) {
          throw new Error(`Response status: ${response.status}`);
        }
    
        const csv = await response.text();
        return csv;
    } catch (error) {
    
    }
}

export async function getFilesData(offset,limit) {
    console.log("[getFilesData]]", offset)
    const url = `${getHost()}/elan-file/files/record_types/org?limit=${limit}&offset=${offset}`;
    try {
        const response = await fetch(url);
        if (!response.ok) {
          throw new Error(`Response status: ${response.status}`);
        }
    
        const json = await response.json();
        return json;
    } catch (error) {
    
    }
    
}

export function getFileName (str) {
    return str.split('\\').pop().split('/').pop();
}
