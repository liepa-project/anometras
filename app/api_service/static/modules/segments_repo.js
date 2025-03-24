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
    
    const url = `${getHost()}/elan-file/files/${file_name}/diff/csv`;
    try {
        const response = await fetch(url);
        if (!response.ok) {
          throw new Error(`Response status: ${response.status}`);
        }
    
        const diff_txt = await response.text();
        const diff_csv = diff_txt.split("\n").map(line => line.split(/;/));
        return diff_csv;
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
export async function getAnnotatorsData(){
    console.log("[getAnnotatorsData]]")
    const url = `${getHost()}/elan-file/annotators`;
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

export async function getFilesData(offset,limit, annotator) {
    console.log("[getFilesData]]", offset)
    var params=""
    if(annotator){
        params="&annotator="+annotator
    }
    const url = `${getHost()}/elan-file/files/record_types/annot1?limit=${limit}&offset=${offset}${params}`;
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
